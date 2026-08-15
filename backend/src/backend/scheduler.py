from __future__ import annotations

from datetime import timedelta

from backend.models import ProjectSnapshot, Task, TaskCreate


class PlanValidationError(ValueError):
    pass


def validate_tasks(tasks: list[TaskCreate]) -> None:
    ids = {task.id for task in tasks}
    if len(ids) != len(tasks):
        raise PlanValidationError("Task IDs must be unique")
    names = [task.name.casefold() for task in tasks]
    if len(names) != len(set(names)):
        raise PlanValidationError("Task names must be unique")
    for task in tasks:
        if set(task.predecessor_ids) - ids:
            raise PlanValidationError(f"{task.name}: unknown predecessor")
        if task.id in task.predecessor_ids:
            raise PlanValidationError(f"{task.name}: a task cannot depend on itself")
    visiting, visited = set(), set()
    by_id = {task.id: task for task in tasks}

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise PlanValidationError("Circular dependency detected")
        if task_id in visited:
            return
        visiting.add(task_id)
        for predecessor_id in by_id[task_id].predecessor_ids:
            visit(predecessor_id)
        visiting.remove(task_id)
        visited.add(task_id)

    for task in tasks:
        visit(task.id)


def schedule(snapshot: ProjectSnapshot) -> list[Task]:
    validate_tasks(snapshot.tasks)
    scheduled: dict[str, Task] = {}
    by_id = {task.id: task for task in snapshot.tasks}

    def calculate(task_id: str) -> Task:
        if task_id in scheduled:
            return scheduled[task_id]
        source = by_id[task_id]
        predecessors = [calculate(item) for item in source.predecessor_ids]
        earliest = max(
            (item.end_date + timedelta(days=1) for item in predecessors),
            default=snapshot.start_date,
        )
        start = earliest + timedelta(days=source.start_offset)
        result = Task(
            **source.model_dump(),
            start_date=start,
            end_date=start + timedelta(days=source.duration - 1),
        )
        scheduled[task_id] = result
        return result

    return [calculate(task.id) for task in snapshot.tasks]
