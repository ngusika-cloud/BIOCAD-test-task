import json

import pytest

from backend.agent import _execute_tool, run_agent
from backend.models import ChatMessage
from backend.store import ProjectStore


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.text = ""

    def raise_for_status(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def iter_lines(self):
        message = self.payload["choices"][0]["message"]
        delta = {key: value for key, value in message.items() if key != "role"}
        chunk = {**self.payload, "choices": [{"delta": delta}]}
        yield f"data: {json.dumps(chunk)}"
        yield "data: [DONE]"


def test_react_agent_executes_tool_and_accumulates_usage(monkeypatch):
    responses = iter(
        [
            {
                "model": "qwen/qwen3.7-flash",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "assign_people",
                                        "arguments": '{"task_id":"analysis","assignees":["Elena","Pavel"]}',
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 10,
                    "total_tokens": 110,
                    "cost": 0.0000043,
                },
            },
            {
                "model": "qwen/qwen3.7-flash",
                "choices": [{"message": {"role": "assistant", "content": "Assigned both people."}}],
                "usage": {
                    "prompt_tokens": 130,
                    "completion_tokens": 12,
                    "total_tokens": 142,
                    "cost": 0.00000546,
                },
            },
        ]
    )

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")
    monkeypatch.setattr(
        "backend.agent.httpx.stream", lambda *args, **kwargs: FakeResponse(next(responses))
    )
    project_store = ProjectStore()

    reply, changes, usage = run_agent(project_store, "Assign Elena and Pavel to Hit analysis")

    hit = next(task for task in project_store.project().tasks if task.id == "analysis")
    assert reply == "Assigned both people."
    assert hit.assignees == ["Elena", "Pavel"]
    assert hit.man_hours == 64
    assert changes[0].task_id == "analysis"
    assert usage.prompt_tokens == 230
    assert usage.completion_tokens == 22
    assert usage.total_tokens == 252
    assert usage.cost_usd == pytest.approx(0.00000976)


def test_agent_sends_history_and_streams_reply(monkeypatch):
    captured = {}
    payload = {
        "model": "qwen/qwen3.7-flash",
        "choices": [{"message": {"role": "assistant", "content": "Which task?"}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
    }

    def fake_stream(*_args, **kwargs):
        captured.update(kwargs["json"])
        return FakeResponse(payload)

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")
    monkeypatch.setattr("backend.agent.httpx.stream", fake_stream)
    tokens = []
    reply, changes, _usage = run_agent(
        ProjectStore(),
        "Move it",
        history=[
            ChatMessage(role="user", content="I need to move a task"),
            ChatMessage(role="assistant", content="Which task do you mean?"),
        ],
        on_token=tokens.append,
    )

    assert reply == "Which task?"
    assert not changes
    assert tokens == ["Which task?"]
    assert captured["stream"] is True
    assert captured["messages"][-3]["content"] == "I need to move a task"
    assert "ask one focused clarification" in captured["messages"][0]["content"]


def test_assignees_can_be_added_and_removed_without_replacing_others():
    project_store = ProjectStore()

    _execute_tool(
        project_store,
        "change_assignees",
        {"task_id": "analysis", "action": "add", "people": ["Pavel"]},
    )
    task = next(item for item in project_store.project().tasks if item.id == "analysis")
    assert task.assignees == ["Anna", "Pavel"]

    _execute_tool(
        project_store,
        "change_assignees",
        {"task_id": "analysis", "action": "remove", "people": ["Anna"]},
    )
    task = next(item for item in project_store.project().tasks if item.id == "analysis")
    assert task.assignees == ["Pavel"]

    result, changes = _execute_tool(
        project_store,
        "change_assignees",
        {"task_id": "analysis", "action": "remove", "people": ["Pavel"]},
    )
    assert result == {"error": "A task must keep at least one assignee"}
    assert not changes


def test_batch_update_changes_many_tasks_in_one_tool_call():
    project_store = ProjectStore()
    _result, changes = _execute_tool(
        project_store,
        "batch_update_tasks",
        {
            "updates": [
                {"task_id": "analysis", "description": "Updated analysis"},
                {"task_id": "screen", "description": "Updated screening"},
            ]
        },
    )

    assert {change.task_id for change in changes} == {"analysis", "screen"}
    snapshots = {task.id: task for task in project_store.snapshot.tasks}
    assert snapshots["analysis"].description == "Updated analysis"
    assert snapshots["screen"].description == "Updated screening"
