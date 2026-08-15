from __future__ import annotations

import os
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.excel import export_excel, parse_excel
from backend.mock_agent import run_mock_command
from backend.models import (
    ChatRequest,
    ChatResponse,
    Project,
    ProjectSnapshot,
    TaskCreate,
    TaskUpdate,
)
from backend.scheduler import PlanValidationError, schedule
from backend.store import store

app = FastAPI(title="PlanPilot API", version="0.1.0")
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
previews: dict[str, ProjectSnapshot] = {}


@app.exception_handler(PlanValidationError)
async def validation_error(_, exc: PlanValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/project", response_model=Project)
def get_project():
    return store.project()


@app.get("/api/tasks")
def get_tasks():
    return store.project().tasks


@app.post("/api/tasks", response_model=Project)
def add_task(task: TaskCreate):
    return store.add(task)


@app.patch("/api/tasks/{task_id}", response_model=Project)
def update_task(task_id: str, update: TaskUpdate):
    try:
        return store.update(task_id, update)
    except KeyError as exc:
        raise HTTPException(404, "Task not found") from exc


@app.delete("/api/tasks/{task_id}", response_model=Project)
def delete_task(task_id: str):
    try:
        return store.delete(task_id)
    except KeyError as exc:
        raise HTTPException(404, "Task not found") from exc


@app.post("/api/project/reset", response_model=Project)
def reset_project():
    return store.reset()


@app.post("/api/project/undo", response_model=Project)
def undo():
    return store.undo()


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    project, changes = run_mock_command(store, request.message)
    count = len(changes)
    return ChatResponse(
        reply=f"Done — {count} task{'s' if count != 1 else ''} updated.",
        changes=changes,
        project=project,
        can_undo=True,
    )


@app.post("/api/import/preview")
async def preview_import(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise PlanValidationError("Choose an .xlsx file")
    snapshot = parse_excel(await file.read(), store.snapshot.name, store.snapshot.start_date)
    token = str(uuid4())
    previews[token] = snapshot
    preview = Project(
        name=snapshot.name,
        start_date=snapshot.start_date,
        tasks=schedule(snapshot),
        revision=store.revision,
    )
    return {"token": token, "project": preview}


@app.post("/api/import/{token}/confirm", response_model=Project)
def confirm_import(token: str):
    snapshot = previews.pop(token, None)
    if snapshot is None:
        raise HTTPException(404, "Import preview expired")
    return store.replace(snapshot)


@app.get("/api/export")
def download_export():
    return Response(
        content=export_excel(store.project()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="planpilot.xlsx"'},
    )


def run():
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
