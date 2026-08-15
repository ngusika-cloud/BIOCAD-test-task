# BIOCAD Gantt chart

BIOCAD Gantt chart is a desktop-first planning workspace for biotech teams. It combines an interactive Gantt chart with natural-language plan editing, validated Excel import/export, multilingual task details, categorical team assignment, and man-hour calculation. Its LangGraph ReAct agent uses Qwen3.7 Flash through OpenRouter.

## What works

- Seed project with 12 tasks, parallel branches, dependencies, and five assignees
- Interactive [SVAR React Gantt](https://svar.dev/react/gantt/) (MIT open-source edition)
- Task selection, details editing, dependency validation, and deletion
- Excel preview, validation, confirmation, export, and round-trip support
- ReAct planning agent with clarification questions, streamed replies, conversation history, and validated planning tools
- Per-run input/output token counts and actual OpenRouter cost reporting
- Seed reset
- FastAPI REST API and a stdio MCP server sharing the same store and scheduler

Example commands: Assign Hit analysis to Elena; Move Primary screening by 3 days; Add a 3-day QA task after Lead selection; Make Candidate review depend on QA; Move all of Anna's tasks by one week.

## Local development

Requirements: Node.js 20+ and Python 3.11+. Install [uv](https://docs.astral.sh/uv/) once if needed.

Backend:

    cd backend
    uv sync --all-groups
    uv run uvicorn backend.main:app --reload

Frontend, in another terminal:

    cd frontend
    npm ci
    npm run dev

Open http://localhost:5173. Vite proxies /api to FastAPI on port 8000.

Verification:

    cd backend
    uv run pytest
    uv run pre-commit run --all-files --config ../.pre-commit-config.yaml
    cd ../frontend
    npm run build

Install the Git hook locally with `cd backend` followed by
`uv run pre-commit install --config ../.pre-commit-config.yaml`.

## Architecture

```mermaid
flowchart TD
    UI[React application] --> Gantt[SVAR Gantt]
    UI -->|REST API| Routes[FastAPI routes]
    MCP[MCP stdio tools] --> Services[Shared project services]
    Routes --> Agent[LangGraph ReAct agent]
    Agent -->|Qwen3.7 Flash| OpenRouter[OpenRouter]
    Agent --> Services
    Services --> Validation[Task and dependency validation]
    Validation --> Scheduler[Deterministic scheduler]
    Scheduler --> Store[In-memory project store]
    Store -->|Scheduled project state| Routes
```

The backend is the source of truth. Every REST or MCP mutation creates a candidate snapshot, validates identifiers and the dependency DAG, and only then commits and recalculates dates. The scheduler uses calendar days; roots begin at the project start, dependent tasks begin the day after their latest predecessor, and explicit move offsets are applied afterward. LLMs never calculate dates.

Data is intentionally in memory for the demo. Restarting the backend restores the seed.

## Excel format

The first row must contain task, description, executor, duration, and predecessors. Executors are comma- or semicolon-separated team members, and predecessors are comma-separated task names. Names must be unique; durations are whole days. See [sample/planpilot-sample.xlsx](sample/planpilot-sample.xlsx).

## API and MCP

REST includes health, project read/reset, task create/update/delete, import preview/confirm, export, agent configuration, regular chat, and SSE streaming chat. Interactive API docs are at http://localhost:8000/docs.

Start MCP with:

    cd backend
    uv run python -m backend.mcp_server

Tools: get_project_state, get_tasks, add_task, update_task, move_task, change_assignees, set_dependencies, and delete_task. They reuse the same business operations as REST.

## Environment

Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`. The default model is `qwen/qwen3.7-flash`; override it with `OPENROUTER_MODEL`. On Render, configure both values on the backend service. `VITE_API_URL` may point the frontend at a separately hosted API.

## Key decisions

- SVAR provides a maintained React-native Gantt instead of a custom timeline.
- Chat chrome is local because the product needs compact, domain-specific change and usage cards; assistant behavior stays behind one API.
- Import is two-phase so users inspect a validated replacement before committing.
- Internal IDs are stable; Excel translates predecessor names only at the boundary.
- OpenRouter's returned usage cost is displayed directly; token-price calculation is only a fallback when a provider omits cost.

## Current limits

State is process-local, dates use calendar days, task bar drag editing is not persisted, agent conversation history is request-local, and there is no authentication or collaboration. See [Roadmap to production](docs/ROADMAP_TO_PRODUCTION.md).
