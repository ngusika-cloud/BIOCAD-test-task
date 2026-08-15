from fastapi.testclient import TestClient

from backend.main import app
from backend.seed import seed_snapshot
from backend.store import store

client = TestClient(app)


def setup_function():
    store.snapshot = seed_snapshot()
    store.revision = 1
    store.undo_snapshot = None


def test_health_and_seed():
    assert client.get("/health").json() == {"status": "ok"}
    assert len(client.get("/api/project").json()["tasks"]) == 12


def test_mock_chat_and_undo():
    response = client.post("/api/chat", json={"message": "Assign Hit analysis to Elena"})
    assert response.status_code == 200
    hit = next(t for t in response.json()["project"]["tasks"] if t["name"] == "Hit analysis")
    assert hit["assignee"] == "Elena"
    assert client.post("/api/project/undo").status_code == 200


def test_mock_rejects_cycle():
    response = client.post(
        "/api/chat", json={"message": "Make Target discovery depend on Candidate review"}
    )
    assert response.status_code == 422
    assert "Circular" in response.json()["detail"]


def test_import_chat_export_round_trip():
    sample = client.get("/api/export").content
    preview = client.post(
        "/api/import/preview",
        files={
            "file": (
                "plan.xlsx",
                sample,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert preview.status_code == 200
    token = preview.json()["token"]
    assert client.post(f"/api/import/{token}/confirm").status_code == 200
    assert (
        client.post("/api/chat", json={"message": "Move Primary screening by 3 days"}).status_code
        == 200
    )
    exported = client.get("/api/export")
    assert exported.status_code == 200
    second_preview = client.post(
        "/api/import/preview",
        files={
            "file": (
                "roundtrip.xlsx",
                exported.content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert second_preview.status_code == 200
