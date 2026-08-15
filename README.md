# BIOCAD Gantt chart

Веб-приложение для планирования проектов: диаграмма Ганта, редактирование задач на естественном языке, импорт и экспорт Excel, проверка зависимостей и расчёт трудозатрат.

## Быстрый запуск

Требования: Python 3.11+, [uv](https://docs.astral.sh/uv/) и Node.js 20+.

```bash
git clone https://github.com/ngusika-cloud/BIOCAD-test-task.git
cd BIOCAD-test-task
cp .env.example .env  # PowerShell: Copy-Item .env.example .env

cd backend
uv sync --all-groups
uv run uvicorn backend.main:app --reload
```

Во втором терминале:

```bash
cd frontend
npm ci
npm run dev
```

Приложение: http://localhost:5173, документация API: http://localhost:8000/docs. В dev-режиме Vite перенаправляет `/api` и `/health` на backend.

## Переменные окружения

Корневой файл `.env` создаётся из `.env.example` и не должен попадать в Git. Опциональная переменная Vite задаётся отдельно в `frontend/.env.local`.

| Переменная | Назначение | Значение по умолчанию |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Ключ OpenRouter; обязателен только для AI-ассистента | — |
| `OPENROUTER_MODEL` | Модель ассистента | `qwen/qwen3.7-flash` |
| `OPENROUTER_SITE_URL` | HTTP Referer для OpenRouter | URL опубликованного приложения |
| `AGENT_MAX_TOOL_CALLS_PER_ROUND` | Максимум операций в одном пакете агента | `10` |
| `AGENT_RECURSION_LIMIT` | Общий предел шагов графа агента | `50` |
| `CORS_ORIGINS` | Разрешённые origin через запятую | `http://localhost:5173` |
| `VITE_API_URL` | Адрес API в `frontend/.env.local` для отдельно размещённого frontend | пусто, используются относительные URL |

## Воспроизводимость и проверки

Версии Python-зависимостей зафиксированы в `backend/uv.lock`, frontend-зависимостей — в `frontend/package-lock.json`. Используйте `uv sync --all-groups` и `npm ci`, не удаляя lock-файлы.

```bash
cd backend
uv run pytest
uv run pre-commit run --all-files --config ../.pre-commit-config.yaml

cd ../frontend
npm run build
```

Pre-commit запускает Ruff для линтинга, сортировки импортов и форматирования. Тестовые Excel-файлы находятся в `sample/`. Данные приложения хранятся в памяти и после перезапуска backend сбрасываются к начальному набору.

## Архитектура и технологии

```mermaid
flowchart LR
    UI[React + SVAR Gantt] -->|REST / SSE| API[FastAPI]
    MCP[MCP-клиент] -->|stdio| MCPServer[MCP-сервер]
    API --> Agent[LangGraph ReAct-агент]
    Agent -->|LLM API| OpenRouter[OpenRouter]
    Agent --> Services[Операции над проектом]
    API --> Services
    MCPServer --> Services
    API <--> Excel[Импорт / экспорт Excel]
    Services --> Validation[Валидация зависимостей]
    Validation --> Scheduler[Расчёт расписания]
    Scheduler --> Store[(In-memory store)]
```

- **Frontend:** React 19, TypeScript, Vite и SVAR React Gantt. UI обращается к backend через REST API и SSE для потоковых ответов ассистента.
- **Backend:** FastAPI, Pydantic и Uvicorn. REST API и stdio MCP-сервер используют единые операции над проектом.
- **Планирование:** детерминированный scheduler проверяет уникальность задач, ссылки и отсутствие циклов, затем рассчитывает даты и человеко-часы. LLM даты не вычисляет.
- **AI:** ReAct-агент на LangGraph вызывает OpenRouter и изменяет план только через валидируемые инструменты.
- **Данные:** in-memory store — осознанное упрощение демонстрационной версии; Excel обрабатывается через openpyxl.

Поддерживаемость обеспечивают разделение моделей, хранилища, планировщика, Excel-адаптера, API и агента; единая бизнес-логика для REST/MCP; типизация; атомарная проверка снимка до сохранения; unit- и API-тесты; Ruff и pre-commit.

## Использование AI

AI использовался как вспомогательный инструмент разработки. В частности, применялись специализированные skills для code review и поддержания качества кода. Итоговые изменения проверялись тестами, статическим анализом и сборкой; ответственность за принятые решения и результат остаётся за разработчиком.

## Ограничения

Нет постоянного хранилища, аутентификации и совместного редактирования; расчёт ведётся в календарных днях. План развития описан в [docs/ROADMAP_TO_PRODUCTION.md](docs/ROADMAP_TO_PRODUCTION.md).

Лицензия: [MIT](LICENSE).
