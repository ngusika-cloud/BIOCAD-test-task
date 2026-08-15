from datetime import date

import pytest

from backend.models import ProjectSnapshot, TaskCreate
from backend.scheduler import PlanValidationError, schedule


def test_scheduler_propagates_dependencies():
    snapshot = ProjectSnapshot(
        name="Test",
        start_date=date(2026, 1, 1),
        tasks=[
            TaskCreate(id="a", name="A", assignee="Anna", duration=3),
            TaskCreate(id="b", name="B", assignee="Ben", duration=2, predecessor_ids=["a"]),
        ],
    )
    result = schedule(snapshot)
    assert result[0].end_date.isoformat() == "2026-01-03"
    assert result[1].start_date.isoformat() == "2026-01-04"


def test_scheduler_rejects_cycle():
    snapshot = ProjectSnapshot(
        name="Test",
        start_date=date(2026, 1, 1),
        tasks=[
            TaskCreate(id="a", name="A", assignee="Anna", duration=1, predecessor_ids=["b"]),
            TaskCreate(id="b", name="B", assignee="Ben", duration=1, predecessor_ids=["a"]),
        ],
    )
    with pytest.raises(PlanValidationError, match="Circular"):
        schedule(snapshot)
