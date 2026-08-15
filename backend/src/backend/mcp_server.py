from mcp.server.fastmcp import FastMCP

from backend.models import TaskCreate, TaskUpdate
from backend.store import store

mcp = FastMCP("BIOCAD Gantt chart")


@mcp.tool()
def get_project_state() -> dict:
    """Return the current scheduled project."""
    return store.project().model_dump(mode="json")


@mcp.tool()
def get_tasks() -> list[dict]:
    """Return all currently scheduled tasks."""
    return [task.model_dump(mode="json") for task in store.project().tasks]


@mcp.tool()
def add_task(
    name: str, description: str, assignees: list[str], duration: int, predecessor_ids: list[str]
) -> dict:
    """Add one validated task and reschedule the project."""
    task = TaskCreate(
        name=name,
        description=description,
        assignees=assignees,
        duration=duration,
        predecessor_ids=predecessor_ids,
    )
    return store.add(task).model_dump(mode="json")


@mcp.tool()
def update_task(
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    assignees: list[str] | None = None,
    duration: int | None = None,
) -> dict:
    """Update one task through shared validation and scheduling."""
    update = TaskUpdate(name=name, description=description, assignees=assignees, duration=duration)
    return store.update(task_id, update).model_dump(mode="json")


@mcp.tool()
def move_task(task_id: str, days_later: int) -> dict:
    """Move a task later by adding a non-negative calendar-day offset."""
    if days_later < 0:
        raise ValueError("days_later must be non-negative")
    task = next((item for item in store.snapshot.tasks if item.id == task_id), None)
    if task is None:
        raise ValueError("Task not found")
    return store.update(
        task_id, TaskUpdate(start_offset=task.start_offset + days_later)
    ).model_dump(mode="json")


@mcp.tool()
def change_assignees(task_id: str, assignees: list[str]) -> dict:
    """Assign a task to one or more team members."""
    return store.update(task_id, TaskUpdate(assignees=assignees)).model_dump(mode="json")


@mcp.tool()
def set_dependencies(task_id: str, predecessor_ids: list[str]) -> dict:
    """Replace task dependencies after graph validation."""
    return store.update(task_id, TaskUpdate(predecessor_ids=predecessor_ids)).model_dump(
        mode="json"
    )


@mcp.tool()
def delete_task(task_id: str) -> dict:
    """Delete one task if nothing depends on it."""
    return store.delete(task_id).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run()
