from __future__ import annotations

import json
import operator
import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated, Literal, TypedDict
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph

from backend.models import AgentUsage, Change, ChatMessage, Person, TaskCreate, TaskUpdate
from backend.store import ProjectStore

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3.7-flash"
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
prompt_environment = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    undefined=StrictUndefined,
    autoescape=False,
    keep_trailing_newline=True,
)


class AgentError(RuntimeError):
    pass


class AgentConfigurationError(AgentError):
    pass


def configured_model() -> str:
    return os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    changes: Annotated[list[Change], operator.add]
    prompt_tokens: Annotated[int, operator.add]
    completion_tokens: Annotated[int, operator.add]
    total_tokens: Annotated[int, operator.add]
    cost_usd: Annotated[float, operator.add]
    model: str


def _estimated_cost(prompt_tokens: int, completion_tokens: int) -> float:
    if prompt_tokens >= 256_000:
        input_price, output_price = 0.20, 0.80
    elif prompt_tokens >= 32_000:
        input_price, output_price = 0.10, 0.40
    else:
        input_price, output_price = 0.03, 0.13
    return (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "assign_people",
            "description": "Replace the people assigned to an existing task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Exact task ID from the plan."},
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string", "enum": [person.value for person in Person]},
                        "minItems": 1,
                    },
                },
                "required": ["task_id", "assignees"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_task",
            "description": "Move an existing task later by a number of calendar days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "days_later": {"type": "integer", "minimum": 0, "maximum": 365},
                },
                "required": ["task_id", "days_later"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Change the name, description, or duration of an existing task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "name": {"type": "string", "minLength": 1, "maxLength": 160},
                    "description": {"type": "string"},
                    "duration": {"type": "integer", "minimum": 1, "maximum": 365},
                },
                "required": ["task_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new task to the plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 160},
                    "description": {"type": "string"},
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string", "enum": [person.value for person in Person]},
                        "minItems": 1,
                    },
                    "duration": {"type": "integer", "minimum": 1, "maximum": 365},
                    "predecessor_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "description", "assignees", "duration", "predecessor_ids"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_dependencies",
            "description": "Replace all predecessor task IDs for an existing task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "predecessor_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["task_id", "predecessor_ids"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task when no other task depends on it.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"],
                "additionalProperties": False,
            },
        },
    },
]


def _task_result(project_store: ProjectStore, task_id: str) -> dict:
    task = next(item for item in project_store.project().tasks if item.id == task_id)
    return task.model_dump(mode="json")


def _execute_tool(
    project_store: ProjectStore, name: str, arguments: dict
) -> tuple[dict, list[Change]]:
    task_id = arguments.get("task_id")
    try:
        if name == "assign_people":
            project_store.update(task_id, TaskUpdate(assignees=arguments["assignees"]))
            people = ", ".join(arguments["assignees"])
            task = _task_result(project_store, task_id)
            change = Change(
                task_id=task_id,
                task_name=task["name"],
                description=f"Assigned to {people}",
            )
        elif name == "move_task":
            source = next(item for item in project_store.snapshot.tasks if item.id == task_id)
            days = arguments["days_later"]
            project_store.update(task_id, TaskUpdate(start_offset=source.start_offset + days))
            task = _task_result(project_store, task_id)
            change = Change(
                task_id=task_id,
                task_name=task["name"],
                description=f"Moved {days} days later",
            )
        elif name == "update_task":
            values = {key: value for key, value in arguments.items() if key != "task_id"}
            project_store.update(task_id, TaskUpdate(**values))
            task = _task_result(project_store, task_id)
            change = Change(
                task_id=task_id,
                task_name=task["name"],
                description="Updated task details",
            )
        elif name == "add_task":
            item = TaskCreate(id=str(uuid4()), **arguments)
            project_store.add(item)
            task_id = item.id
            task = _task_result(project_store, task_id)
            change = Change(
                task_id=task_id,
                task_name=task["name"],
                description="Added task",
            )
        elif name == "set_dependencies":
            project_store.update(task_id, TaskUpdate(predecessor_ids=arguments["predecessor_ids"]))
            task = _task_result(project_store, task_id)
            change = Change(
                task_id=task_id,
                task_name=task["name"],
                description="Updated dependencies",
            )
        elif name == "delete_task":
            source = next(item for item in project_store.snapshot.tasks if item.id == task_id)
            project_store.delete(task_id)
            return {"deleted_task_id": task_id}, [
                Change(task_id=task_id, task_name=source.name, description="Deleted task")
            ]
        else:
            return {"error": f"Unknown tool: {name}"}, []
    except (KeyError, StopIteration, ValueError) as exc:
        return {"error": str(exc) or "Task not found"}, []
    return task, [change]


def _system_prompt(project_store: ProjectStore) -> str:
    project = project_store.project()
    plan = [
        {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "assignees": task.assignees,
            "duration": task.duration,
            "predecessor_ids": task.predecessor_ids,
            "start_offset": task.start_offset,
        }
        for task in project.tasks
    ]
    return prompt_environment.get_template("planning_agent.j2").render(
        available_people=", ".join(project.team),
        current_plan=json.dumps(plan, ensure_ascii=False, default=str),
    )


def run_agent(
    project_store: ProjectStore,
    message: str,
    history: Sequence[ChatMessage] = (),
    on_token: Callable[[str], None] | None = None,
) -> tuple[str, list[Change], AgentUsage]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key or api_key.startswith("sk-or-v1-your-key"):
        raise AgentConfigurationError("OPENROUTER_API_KEY is not configured")
    requested_model = configured_model()

    def call_model(state: AgentState) -> AgentState:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv(
                "OPENROUTER_SITE_URL", "https://biocad-test-task-1.onrender.com"
            ),
            "X-Title": "BIOCAD Gantt chart",
        }
        try:
            with httpx.stream(
                "POST",
                OPENROUTER_URL,
                headers=headers,
                json={
                    "model": requested_model,
                    "messages": state["messages"],
                    "tools": TOOLS,
                    "tool_choice": "auto",
                    "temperature": 0.1,
                    "reasoning": {"effort": "none", "exclude": True},
                    "stream": True,
                    "stream_options": {"include_usage": True},
                },
                timeout=90,
            ) as response:
                response.raise_for_status()
                content_parts: list[str] = []
                tool_calls: dict[int, dict] = {}
                usage: dict = {}
                response_model = requested_model
                for line in response.iter_lines():
                    if not line or line.startswith(":") or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    payload = json.loads(data)
                    if payload.get("error"):
                        error = payload["error"]
                        raise AgentError(error.get("message", str(error)))
                    response_model = payload.get("model") or response_model
                    if payload.get("usage"):
                        usage = payload["usage"]
                    choices = payload.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    if delta.get("content"):
                        fragment = delta["content"]
                        content_parts.append(fragment)
                        if on_token:
                            on_token(fragment)
                    for fragment in delta.get("tool_calls") or []:
                        index = int(fragment.get("index", 0))
                        target = tool_calls.setdefault(
                            index,
                            {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            },
                        )
                        target["id"] += fragment.get("id") or ""
                        function = fragment.get("function") or {}
                        target["function"]["name"] += function.get("name") or ""
                        target["function"]["arguments"] += function.get("arguments") or ""
        except (httpx.HTTPError, ValueError) as exc:
            raise AgentError(f"OpenRouter request failed: {exc}") from exc

        if not content_parts and not tool_calls:
            raise AgentError("OpenRouter returned no assistant response")
        assistant_message = {
            "role": "assistant",
            "content": "".join(content_parts),
        }
        if tool_calls:
            assistant_message["tool_calls"] = [tool_calls[index] for index in sorted(tool_calls)]
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        cost = usage.get("cost")
        if cost is None:
            cost = _estimated_cost(prompt_tokens, completion_tokens)
        return {
            "messages": [assistant_message],
            "changes": [],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": int(usage.get("total_tokens") or prompt_tokens + completion_tokens),
            "cost_usd": float(cost),
            "model": response_model,
        }

    def call_tools(state: AgentState) -> AgentState:
        tool_messages = []
        changes = []
        for tool_call in state["messages"][-1].get("tool_calls", []):
            function = tool_call["function"]
            try:
                arguments = json.loads(function.get("arguments") or "{}")
                result, tool_changes = _execute_tool(project_store, function["name"], arguments)
            except (TypeError, ValueError) as exc:
                result, tool_changes = {"error": f"Invalid tool arguments: {exc}"}, []
            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function["name"],
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )
            changes.extend(tool_changes)
        return {
            "messages": tool_messages,
            "changes": changes,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0,
            "model": state["model"],
        }

    def route(state: AgentState) -> Literal["tools", "end"]:
        return "tools" if state["messages"][-1].get("tool_calls") else "end"

    builder = StateGraph(AgentState)
    builder.add_node("model", call_model)
    builder.add_node("tools", call_tools)
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", route, {"tools": "tools", "end": END})
    builder.add_edge("tools", "model")
    graph = builder.compile()
    initial: AgentState = {
        "messages": [
            {"role": "system", "content": _system_prompt(project_store)},
            *(item.model_dump() for item in history),
            {"role": "user", "content": message},
        ],
        "changes": [],
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0,
        "model": requested_model,
    }
    try:
        result = graph.invoke(initial, config={"recursion_limit": 12})
    except GraphRecursionError as exc:
        raise AgentError("The planning agent exceeded its tool-call limit") from exc
    final_message = result["messages"][-1]
    reply = final_message.get("content") or "The requested plan operations are complete."
    usage = AgentUsage(
        model=result["model"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
        total_tokens=result["total_tokens"],
        cost_usd=result["cost_usd"],
    )
    return reply, result["changes"], usage
