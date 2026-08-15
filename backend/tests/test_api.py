from fastapi.testclient import TestClient

import backend.main as main_module
from backend.main import app
from backend.models import AgentUsage, Change, TaskUpdate
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


def test_agent_chat_response(monkeypatch):
    def fake_agent(project_store, _message, **_kwargs):
        project_store.update("analysis", TaskUpdate(assignees=["Elena"]))
        return (
            "Assigned Hit analysis to Elena.",
            [Change(task_id="analysis", task_name="Hit analysis", description="Assigned to Elena")],
            AgentUsage(
                model="qwen/qwen3.7-flash",
                prompt_tokens=100,
                completion_tokens=20,
                total_tokens=120,
                cost_usd=0.0000056,
            ),
        )

    monkeypatch.setattr(main_module, "run_agent", fake_agent)
    response = client.post("/api/chat", json={"message": "Assign Hit analysis to Elena"})
    assert response.status_code == 200
    hit = next(t for t in response.json()["project"]["tasks"] if t["name"] == "Hit analysis")
    assert hit["assignees"] == ["Elena"]
    assert hit["man_hours"] == 32
    assert response.json()["usage"]["total_tokens"] == 120
    assert response.json()["usage"]["cost_usd"] == 0.0000056


def test_agent_config_and_stream(monkeypatch):
    def fake_agent(project_store, _message, **kwargs):
        kwargs["on_token"]("Need ")
        kwargs["on_token"]("details.")
        return "Need details.", [], AgentUsage(model="test/model", total_tokens=7)

    monkeypatch.setenv("OPENROUTER_MODEL", "test/model")
    monkeypatch.setattr(main_module, "run_agent", fake_agent)
    assert client.get("/api/agent/config").json() == {"model": "test/model"}

    response = client.post(
        "/api/chat/stream",
        json={
            "message": "Move it",
            "history": [{"role": "assistant", "content": "Which task?"}],
        },
    )
    assert response.status_code == 200
    assert "event: token\ndata:" in response.text
    assert "event: result\ndata:" in response.text
    assert '"model": "test/model"' in response.text


def test_agent_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    response = client.post("/api/chat", json={"message": "Move a task"})
    assert response.status_code == 503
    assert "OPENROUTER_API_KEY" in response.json()["detail"]


def test_import_chat_export_round_trip(monkeypatch):
    def fake_agent(project_store, _message, **_kwargs):
        task = next(
            item for item in project_store.snapshot.tasks if item.name == "Primary screening"
        )
        project_store.update(task.id, TaskUpdate(start_offset=task.start_offset + 3))
        return (
            "Moved Primary screening.",
            [Change(task_id=task.id, task_name=task.name, description="Moved 3 days later")],
            AgentUsage(model="qwen/qwen3.7-flash"),
        )

    monkeypatch.setattr(main_module, "run_agent", fake_agent)
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
