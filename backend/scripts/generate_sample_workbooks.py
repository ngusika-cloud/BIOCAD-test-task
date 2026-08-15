from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.excel import export_excel, parse_excel
from backend.models import Project, ProjectSnapshot, TaskCreate
from backend.scheduler import schedule

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "sample" / "import-tests"
ASSIGNEES = ["Anna", "Elena", "Mikhail", "Daria", "Pavel"]
ACTIVITIES = [
    "Scope definition",
    "Protocol design",
    "Material preparation",
    "Method development",
    "Experiment execution",
    "Quality review",
    "Data analysis",
    "Evidence review",
    "Documentation",
    "Readiness review",
]


def dependency_indices(index: int) -> list[int]:
    """Create parallel pairs followed by merge points without introducing cycles."""
    if index == 0:
        return []
    position = index % 5
    if position in (1, 2):
        return [index - position]
    if position == 3:
        return [index - 2, index - 1]
    return [index - 1]


def generated_snapshot(task_count: int, title: str) -> ProjectSnapshot:
    ids = [f"task-{index + 1:03d}" for index in range(task_count)]
    tasks = []
    for index, task_id in enumerate(ids):
        activity = ACTIVITIES[index % len(ACTIVITIES)]
        phase = index // 5 + 1
        tasks.append(
            TaskCreate(
                id=task_id,
                name=f"Phase {phase:02d} - {activity}",
                description=f"Import test activity {index + 1} for {title}.",
                assignee=ASSIGNEES[index % len(ASSIGNEES)],
                duration=(index % 7) + 1,
                predecessor_ids=[ids[item] for item in dependency_indices(index)],
            )
        )
    return ProjectSnapshot(name=title, start_date=date(2026, 9, 1), tasks=tasks)


def quick_snapshot() -> ProjectSnapshot:
    tasks = [
        TaskCreate(
            id="requirements",
            name="Requirements",
            description="Agree scope and acceptance criteria.",
            assignee="Anna",
            duration=2,
        ),
        TaskCreate(
            id="design",
            name="Solution design",
            description="Prepare the implementation design.",
            assignee="Elena",
            duration=3,
            predecessor_ids=["requirements"],
        ),
        TaskCreate(
            id="build",
            name="Implementation",
            description="Build and review the solution.",
            assignee="Mikhail",
            duration=5,
            predecessor_ids=["design"],
        ),
        TaskCreate(
            id="release",
            name="Release",
            description="Complete final verification and release.",
            assignee="Daria",
            duration=1,
            predecessor_ids=["build"],
        ),
    ]
    return ProjectSnapshot(name="Quick import test", start_date=date(2026, 9, 1), tasks=tasks)


def write_and_verify(filename: str, snapshot: ProjectSnapshot) -> None:
    tasks = schedule(snapshot)
    project = Project(name=snapshot.name, start_date=snapshot.start_date, tasks=tasks)
    content = export_excel(project)
    target = OUTPUT_DIR / filename
    target.write_bytes(content)
    imported = parse_excel(content, snapshot.name, snapshot.start_date)
    assert len(imported.tasks) == len(snapshot.tasks)
    assert [task.name for task in imported.tasks] == [task.name for task in snapshot.tasks]
    schedule(imported)
    print(f"created {target.name}: {len(imported.tasks)} tasks")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = [
        ("01-quick-4-tasks.xlsx", quick_snapshot()),
        ("02-small-10-tasks.xlsx", generated_snapshot(10, "Small import test")),
        ("03-medium-25-tasks.xlsx", generated_snapshot(25, "Medium import test")),
        ("04-large-60-tasks.xlsx", generated_snapshot(60, "Large import test")),
    ]
    for filename, snapshot in fixtures:
        write_and_verify(filename, snapshot)


if __name__ == "__main__":
    main()
