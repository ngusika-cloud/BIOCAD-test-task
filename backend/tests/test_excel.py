from io import BytesIO

import pytest
from openpyxl import Workbook

from backend.excel import export_excel, parse_excel
from backend.scheduler import PlanValidationError
from backend.seed import seed_snapshot
from backend.store import ProjectStore


def workbook(rows):
    book = Workbook()
    sheet = book.active
    sheet.append(["task", "description", "executor", "duration", "predecessors"])
    for row in rows:
        sheet.append(row)
    data = BytesIO()
    book.save(data)
    return data.getvalue()


def test_excel_round_trip():
    source = ProjectStore()
    data = export_excel(source.project())
    parsed = parse_excel(data, "Imported", source.snapshot.start_date)
    assert len(parsed.tasks) == 12
    assert parsed.tasks[-1].predecessor_ids


def test_excel_unknown_predecessor():
    with pytest.raises(PlanValidationError, match="unknown predecessor"):
        parse_excel(
            workbook([["Test", "", "Anna", 2, "Missing"]]), "Test", seed_snapshot().start_date
        )
