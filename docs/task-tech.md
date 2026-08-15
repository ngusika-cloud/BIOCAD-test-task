# BIOCAD Test Task — Thesis Plan

## 1. Fix the product
- Working name: **PlanPilot**
- Gantt — the main working screen
- AI chat — a way to manage the plan in natural language
- Main flow:
  - open the app
  - see the seed Gantt
  - upload Excel
  - modify the plan via AI
  - see the changes immediately in the Gantt
  - open the task
  - export Excel
- Do not add features outside the core flow unless necessary

## 2. Set up the project skeleton
- `frontend/` — React + TypeScript
- `backend/` — Python + FastAPI
- `sample/` — test Excel
- `docs/`
- `README.md`
- `docs/ROADMAP_TO_PRODUCTION.md`
- `.env.example`
- Set up Git
- Store OpenRouter key only on the backend

## 3. Create the data model
- `Project`
- `Task`: id, name, description, assignee, duration, predecessor_ids, start_date, end_date
- Use internal IDs, not task names

## 4. Implement the scheduler
- Project start date
- Tasks without predecessors start from the project start
- Tasks with predecessors start after the dependencies are completed
- Calendar days for MVP
- Checks: unknown predecessor, self-dependency, circular dependency
- Scheduler is deterministic
- LLM does not calculate dates on its own

## 5. Create seed data
- 10–15 realistic tasks
- 4–5 performers
- Several parallel branches and dependency chains
- The seed should look good on the Gantt chart and be suitable for the AI demo

## 6. Create a backend API without AI
- `GET /health`
- `GET /api/project`
- CRUD tasks
- reset seed
- import Excel
- export Excel
- undo
- Backend — source of truth
- REST and MCP use the same business logic

## 7. Create a Gantt UI
- React Gantt library, don’t write the Gantt from scratch
- Timeline, task bars, task names, selected/hover states
- Dependency lines, if the library supports them
- Horizontal scroll
- Click on a task → modal/drawer

## 8. Create a Task Modal
- Name
- Description
- Assigned to
- Duration
- Start / End
- Predecessors
- Editing
- After the change → backend validation → scheduler → Gantt update

## 9. Perform Excel Import
Required columns:
- `task`
- `description`
- `executor`
- `duration`
- `predecessors`

Check:
- missing columns
- empty task name
- duplicate names
- invalid duration
- unknown predecessor
- self-dependency
- cycle

UX:
- select a file
- show preview
- confirm import
- replace the current project
- show errors in clear language

## 10. Create an Excel Export
- Export the current project state
- The same required columns
- Internal predecessor IDs → task names
- Check the round‑trip: import → change → export → re‑import

## 11. Connect MCP
Main tools:
- `get_project_state`
- `get_tasks`
- `add_task`
- `update_task`
- `move_task`
- `change_assignee`
- `set_dependencies`
- `delete_task`

Rules:
- strict schemas
- all mutations go through backend validation
- MCP uses the same business logic as REST
- no unrestricted `edit_project`

## 12. Connect OpenRouter
- API key only for backend
- Model via env
- FastAPI calls OpenRouter
- LLM understands the intent, receives the project context, calls MCP tools, and briefly reports the result
- LLM does not modify the state directly

## 13. Debug AI happy paths
Check:
- `Assign Backend API to Anna`
- `Move Backend API by 3 days`
- `Add a 3‑day QA task after Backend API`
- `Make Launch depend on QA`
- `Move all of Anna's tasks by one week`
- multi‑step instruction
- invalid/circular dependency

## 14. Create a good AI UX
- Empty state with command examples
- Loading: `Understanding your request…` → `Updating project…`
- After the operation, show how many tasks have changed and what exactly has changed
- Briefly highlight the changed tasks on the Gantt
- Do not show raw reasoning / tool internals

## 15. Add Undo
- Save `before_state` before the AI mutation
- After a successful operation, save the changeset
- Show `Undo` in the chat
- Minimum one-step undo
- Use as a trust mechanism for bulk AI actions

## 16. Handle errors
- OpenRouter failure
- Model timeout
- Invalid tool call
- Invalid Excel
- Unknown task / no matching tasks
- Circular dependency
- Invalid duration
- Backend failure
- Do not show the stack trace to the user

## 17. Perform UI polish
- Desktop-first
- Gantt ~70–75%
- Chat ~25–30%
- Consistent spacing / typography / buttons
- Calm SaaS-style
- No unnecessary AI gradients / robot visuals
- Check 13–16" screen
- Basic mobile fallback

## 18. Run tests
Backend:
- scheduler
- cycles
- Excel parser
- mutations
- dependency propagation
- MCP validation

AI:
- 15–20 fixed prompts
- expected tool
- expected state change
- pass/fail

## 19. Verify end-to-end scenario
- open deployed app
- seed Gantt loaded
- import sample Excel
- bulk edit via AI
- add task/dependency via AI
- open task modal
- undo
- export Excel
- re-import export
- everything works without localhost

## 20. Prepare the README
- product description
- live demo
- demo video/gif
- key features
- architecture
- MCP tools
- scheduling assumptions
- Excel format
- local run
- env variables
- deployment
- product/technical decisions
- AI-assisted development
- limitations
- link to Roadmap to Production

## 21. Prepare the Roadmap to Production
### P0 — Reliability
- PostgreSQL
- persistence
- transactions
- revision history
- backups

### P1 — Security
- auth
- RBAC
- SSO
- rate limits
- secret management
- audit log

### P1 — AI Quality
- regression evals
- prompt versioning
- tracing
- model fallback
- cost/latency monitoring
- confirmations for risky actions

### P2+
- collaboration
- large-project scalability
- Jira / Linear / Sheets integrations

## 22. Create a demo video
Scenario:
1. open the app
2. show the seed Gantt
3. import Excel
4. perform bulk AI edit
5. add a task via AI
6. show the updated Gantt
7. open the task modal
8. export Excel

Goal: 60–90 seconds.

## 23. Prepare the protection
Structure:
1. Problem
2. Product concept
3. Live demo
4. UX decisions
5. Architecture
6. Why MCP
7. Guardrails / reliability
8. Trade-offs
9. Roadmap to Production
10. Metrics / next steps

Prepare answers:
- Why MCP?
- Why this model?
- What if the LLM makes a mistake?
- What if the query is ambiguous?
- How are cycles prevented?
- Why is the scheduler deterministic?
- Why is there Undo?
- Why no database/auth?
- How was the AI tested?
- How to get it to production?

## 24. Final readiness criterion
The project is ready if the reviewer, without your help, can:
- open the public URL
- understand the product
- see the Gantt chart
- import Excel
- change the plan via AI
- understand what has changed
- undo a change
- open a task
- export a new Excel
- understand the architecture and limitations from the README
