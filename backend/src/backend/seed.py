from datetime import date

from backend.models import ProjectSnapshot, TaskCreate


def seed_snapshot() -> ProjectSnapshot:
    rows = [
        (
            "discovery",
            "Target discovery",
            "Define target profile and evidence package",
            "Elena",
            4,
            [],
        ),
        (
            "assay",
            "Assay development",
            "Build and qualify the primary screening assay",
            "Mikhail",
            6,
            ["discovery"],
        ),
        (
            "library",
            "Compound library prep",
            "Curate and plate the focused compound library",
            "Daria",
            5,
            ["discovery"],
        ),
        (
            "screen",
            "Primary screening",
            "Run screen and complete quality control",
            "Mikhail",
            8,
            ["assay", "library"],
        ),
        (
            "analysis",
            "Hit analysis",
            "Normalize results and select confirmed hits",
            "Anna",
            4,
            ["screen"],
        ),
        (
            "confirm",
            "Hit confirmation",
            "Dose response and orthogonal confirmation",
            "Elena",
            7,
            ["analysis"],
        ),
        (
            "adme",
            "Early ADME",
            "In vitro stability and permeability panel",
            "Daria",
            6,
            ["analysis"],
        ),
        (
            "tox",
            "Safety panel",
            "Early off-target and cytotoxicity panel",
            "Pavel",
            5,
            ["analysis"],
        ),
        (
            "lead",
            "Lead selection",
            "Review evidence and nominate lead series",
            "Anna",
            3,
            ["confirm", "adme", "tox"],
        ),
        (
            "process",
            "Process development",
            "Develop initial synthesis and control strategy",
            "Elena",
            7,
            ["lead"],
        ),
        (
            "regulatory",
            "Regulatory package",
            "Prepare pre-IND briefing materials",
            "Pavel",
            6,
            ["lead"],
        ),
        (
            "launch",
            "Candidate review",
            "Cross-functional candidate readiness review",
            "Anna",
            2,
            ["process", "regulatory"],
        ),
    ]
    return ProjectSnapshot(
        name="Biotech launch plan",
        start_date=date(2026, 8, 17),
        tasks=[
            TaskCreate(
                id=i,
                name=n,
                description=d,
                assignees=[a],
                duration=days,
                predecessor_ids=deps,
            )
            for i, n, d, a, days, deps in rows
        ],
    )
