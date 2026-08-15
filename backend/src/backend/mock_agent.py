from __future__ import annotations

import re
from copy import deepcopy
from uuid import uuid4

from backend.models import Change, ProjectSnapshot, TaskCreate
from backend.scheduler import PlanValidationError
from backend.store import ProjectStore


def _find_task(snapshot: ProjectSnapshot, query: str) -> TaskCreate:
    query = query.strip().casefold()
    exact = [task for task in snapshot.tasks if task.name.casefold() == query]
    matches = exact or [
        task
        for task in snapshot.tasks
        if task.name.casefold() in query or query in task.name.casefold()
    ]
    if len(matches) != 1:
        raise PlanValidationError("I could not identify exactly one task. Try using its full name.")
    return matches[0]


def run_mock_command(project_store: ProjectStore, message: str):
    text = message.strip()
    candidate = deepcopy(project_store.snapshot)
    changes: list[Change] = []
    assign = re.search(r"(?:assign|reassign)\s+(.+?)\s+to\s+([\w -]+)$", text, re.I)
    move = re.search(r"move\s+(.+?)\s+by\s+(\d+)\s+days?", text, re.I)
    add = re.search(r"add\s+(?:a\s+)?(\d+)[- ]day\s+(.+?)\s+(?:task\s+)?after\s+(.+)$", text, re.I)
    depend = re.search(r"make\s+(.+?)\s+depend\s+on\s+(.+)$", text, re.I)
    bulk = re.search(
        r"move\s+all\s+of\s+(.+?)(?:'s|’s)\s+tasks?\s+by\s+(?:one|1)\s+week", text, re.I
    )
    if bulk:
        assignee = bulk.group(1).strip()
        targets = [
            task for task in candidate.tasks if task.assignee.casefold() == assignee.casefold()
        ]
        if not targets:
            raise PlanValidationError(f"No tasks are assigned to {assignee}.")
        for task in targets:
            task.start_offset += 7
            changes.append(
                Change(task_id=task.id, task_name=task.name, description="Moved 7 days later")
            )
    elif assign:
        task = _find_task(candidate, assign.group(1))
        task.assignee = assign.group(2).strip()
        changes.append(
            Change(task_id=task.id, task_name=task.name, description=f"Assigned to {task.assignee}")
        )
    elif move:
        task = _find_task(candidate, move.group(1))
        days = int(move.group(2))
        task.start_offset += days
        changes.append(
            Change(task_id=task.id, task_name=task.name, description=f"Moved {days} days later")
        )
    elif add:
        predecessor = _find_task(candidate, add.group(3))
        task = TaskCreate(
            id=str(uuid4()),
            name=add.group(2).strip().title(),
            description="Added through the mock planning assistant",
            assignee=predecessor.assignee,
            duration=int(add.group(1)),
            predecessor_ids=[predecessor.id],
        )
        candidate.tasks.append(task)
        changes.append(
            Change(
                task_id=task.id, task_name=task.name, description=f"Added after {predecessor.name}"
            )
        )
    elif depend:
        task = _find_task(candidate, depend.group(1))
        predecessor = _find_task(candidate, depend.group(2))
        task.predecessor_ids = list(dict.fromkeys([*task.predecessor_ids, predecessor.id]))
        changes.append(
            Change(
                task_id=task.id,
                task_name=task.name,
                description=f"Now depends on {predecessor.name}",
            )
        )
    else:
        raise PlanValidationError(
            "This mock understands assignment, moving, adding a task after another task, and setting a dependency."
        )
    return project_store.replace(candidate), changes
