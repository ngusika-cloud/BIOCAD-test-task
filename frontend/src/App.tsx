import { Gantt, Willow, type IApi, type ITask } from "@svar-ui/react-gantt";
import "@svar-ui/react-gantt/all.css";
import {
  Bot,
  CalendarDays,
  Check,
  Download,
  FileSpreadsheet,
  FlaskConical,
  GripVertical,
  LoaderCircle,
  Send,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState, type FormEvent, type PointerEvent } from "react";

import { api } from "./api";
import type { AgentUsage, Change, Person, Project, Task } from "./types";

type ChatItem = {
  role: "assistant" | "user";
  text: string;
  changes?: Change[];
  usage?: AgentUsage;
  streaming?: boolean;
};
type Language = "en" | "ru";
type TimelineScale = "week" | "month" | "quarter";

const translations = {
  en: {
    demo: "Demo",
    importExcel: "Import Excel",
    export: "Export",
    projectTimeline: "Project timeline",
    live: "Live",
    tasks: "tasks",
    updated: "Updated just now",
    today: "Today",
    week: "Week",
    month: "Month",
    quarter: "Quarter",
    startDate: "Start date",
    targetCompletion: "Target completion",
    totalManHours: "Total man-hours",
    team: "Team",
    task: "Task",
    start: "Start",
    days: "Days",
    hours: "Hours",
    planned: "Planned",
    recentlyChanged: "Recently changed",
    selectHint: "Select any task to view and edit details",
    assistant: "Planning assistant",
    agentReady: "ReAct agent · Ready",
    welcome: "I’m your planning copilot. Tell me what to change and I’ll update the schedule instantly.",
    tryCommand: "Try a command",
    updating: "Updating project…",
    askPlaceholder: "Ask me to update the plan…",
    sendHint: "Enter to send · Shift + Enter for new line",
    send: "Send",
    taskDetails: "Task details",
    close: "Close",
    taskName: "Task name",
    description: "Description",
    assignees: "Assignees",
    selectPeople: "Select team members",
    duration: "Duration (days)",
    scheduledWindow: "Scheduled window",
    taskManHours: "Task man-hours",
    predecessors: "Predecessors",
    deleteTask: "Delete task",
    deleteConfirm: "Delete this task?",
    cancel: "Cancel",
    saveChanges: "Save changes",
    saveError: "Could not save task",
    deleteError: "Could not delete task",
    importPreview: "Import preview",
    replacePlan: "Replace current plan?",
    valid: "Valid",
    importDescription:
      "The workbook passed column, duration, predecessor, and cycle validation. Confirming will replace the current plan.",
    moreTasks: "more tasks",
    importPlan: "Import plan",
    loading: "Loading your plan…",
    importSuccess: "Excel imported successfully. The new plan is ready.",
    importFailed: "Import failed",
    workbookError: "Could not read workbook",
    requestError: "I couldn't apply that change.",
    resizeAssistant: "Resize planning assistant",
    peopleSelected: "selected",
    tokenUsage: "tokens",
    inputTokens: "input",
    outputTokens: "output",
    runCost: "cost",
    clearChat: "Clear chat",
    model: "Model",
  },
  ru: {
    demo: "Демо",
    importExcel: "Импорт Excel",
    export: "Экспорт",
    projectTimeline: "График проекта",
    live: "Активен",
    tasks: "задач",
    updated: "Обновлено только что",
    today: "Сегодня",
    week: "Неделя",
    month: "Месяц",
    quarter: "Квартал",
    startDate: "Дата начала",
    targetCompletion: "Плановое завершение",
    totalManHours: "Всего человеко-часов",
    team: "Команда",
    task: "Задача",
    start: "Начало",
    days: "Дни",
    hours: "Часы",
    planned: "Запланировано",
    recentlyChanged: "Недавно изменено",
    selectHint: "Выберите задачу, чтобы посмотреть или изменить её",
    assistant: "Помощник по планированию",
    agentReady: "ReAct-агент · Готов",
    welcome: "Я ваш помощник по планированию. Опишите изменение, и я сразу обновлю график.",
    tryCommand: "Пример команды",
    updating: "Обновляю проект…",
    askPlaceholder: "Попросите меня изменить план…",
    sendHint: "Enter — отправить · Shift + Enter — новая строка",
    send: "Отправить",
    taskDetails: "Параметры задачи",
    close: "Закрыть",
    taskName: "Название задачи",
    description: "Описание",
    assignees: "Исполнители",
    selectPeople: "Выберите участников",
    duration: "Длительность (дни)",
    scheduledWindow: "Плановый период",
    taskManHours: "Человеко-часы задачи",
    predecessors: "Предшествующие задачи",
    deleteTask: "Удалить задачу",
    deleteConfirm: "Удалить эту задачу?",
    cancel: "Отмена",
    saveChanges: "Сохранить",
    saveError: "Не удалось сохранить задачу",
    deleteError: "Не удалось удалить задачу",
    importPreview: "Предпросмотр импорта",
    replacePlan: "Заменить текущий план?",
    valid: "Проверено",
    importDescription:
      "Файл прошёл проверку столбцов, длительности, зависимостей и циклов. Подтверждение заменит текущий план.",
    moreTasks: "задач ещё",
    importPlan: "Импортировать план",
    loading: "Загружаю план…",
    importSuccess: "Excel успешно импортирован. Новый план готов.",
    importFailed: "Ошибка импорта",
    workbookError: "Не удалось прочитать файл",
    requestError: "Не удалось применить изменение.",
    resizeAssistant: "Изменить ширину помощника",
    peopleSelected: "выбрано",
    tokenUsage: "токенов",
    inputTokens: "вход",
    outputTokens: "выход",
    runCost: "стоимость",
    clearChat: "Очистить чат",
    model: "Модель",
  },
} satisfies Record<Language, Record<string, string>>;

const examples: Record<Language, string[]> = {
  en: [
    "Assign Hit analysis to Elena",
    "Move Primary screening by 3 days",
    "Add a 3-day QA task after Lead selection",
    "Move all of Anna's tasks by one week",
  ],
  ru: [
    "Assign Hit analysis to Elena",
    "Move Primary screening by 3 days",
    "Add a 3-day QA task after Lead selection",
    "Move all of Anna's tasks by one week",
  ],
};

function dateLabel(value: string, language: Language) {
  return new Intl.DateTimeFormat(language === "ru" ? "ru-RU" : "en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function isoWeek(date: Date) {
  const target = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = target.getUTCDay() || 7;
  target.setUTCDate(target.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1));
  return Math.ceil(((target.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
}

function TaskModal({
  task,
  project,
  language,
  onClose,
  onSave,
  onDelete,
}: {
  task: Task;
  project: Project;
  language: Language;
  onClose: () => void;
  onSave: (body: object) => Promise<void>;
  onDelete: () => Promise<void>;
}) {
  const t = translations[language];
  const [form, setForm] = useState({ ...task });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const currentHours = Number(form.duration) * 8 * form.assignees.length;

  const togglePerson = (person: Person) => {
    const selected = form.assignees.includes(person);
    if (selected && form.assignees.length === 1) return;
    setForm({
      ...form,
      assignees: selected
        ? form.assignees.filter((item) => item !== person)
        : [...form.assignees, person],
    });
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onSave({
        name: form.name,
        description: form.description,
        assignees: form.assignees,
        duration: Number(form.duration),
        predecessor_ids: form.predecessor_ids,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.saveError);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="task-title">
        <div className="modal-head">
          <div>
            <span className="eyebrow">{t.taskDetails}</span>
            <h2 id="task-title">{task.name}</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label={t.close}>
            <X size={19} />
          </button>
        </div>
        <form onSubmit={submit}>
          <label>
            {t.taskName}
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label>
            {t.description}
            <textarea rows={4} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </label>
          <div className="form-grid">
            <label>
              {t.assignees}
              <details className="people-select">
                <summary>
                  <span>{form.assignees.join(", ") || t.selectPeople}</span>
                  <small>{form.assignees.length} {t.peopleSelected}</small>
                </summary>
                <div className="people-options">
                  {project.team.map((person) => (
                    <label key={person}>
                      <input
                        type="checkbox"
                        checked={form.assignees.includes(person)}
                        disabled={form.assignees.length === 1 && form.assignees.includes(person)}
                        onChange={() => togglePerson(person)}
                      />
                      <i>{initials(person)}</i>
                      <span>{person}</span>
                    </label>
                  ))}
                </div>
              </details>
            </label>
            <label>
              {t.duration}
              <input type="number" min="1" max="365" value={form.duration} onChange={(event) => setForm({ ...form, duration: Number(event.target.value) })} />
            </label>
          </div>
          <div className="task-facts">
            <div className="date-card">
              <CalendarDays size={17} />
              <div>
                <span>{t.scheduledWindow}</span>
                <strong>{dateLabel(task.start_date, language)} — {dateLabel(task.end_date, language)}</strong>
              </div>
            </div>
            <div className="date-card hours-card">
              <strong>{currentHours}</strong>
              <div>
                <span>{t.taskManHours}</span>
                <small>{form.duration} × 8 × {form.assignees.length}</small>
              </div>
            </div>
          </div>
          <fieldset>
            <legend>{t.predecessors}</legend>
            <div className="check-list">
              {project.tasks.filter((item) => item.id !== task.id).map((item) => (
                <label className="check-row" key={item.id}>
                  <input
                    type="checkbox"
                    checked={form.predecessor_ids.includes(item.id)}
                    onChange={(event) => setForm({
                      ...form,
                      predecessor_ids: event.target.checked
                        ? [...form.predecessor_ids, item.id]
                        : form.predecessor_ids.filter((id) => id !== item.id),
                    })}
                  />
                  <span>{item.name}</span>
                </label>
              ))}
            </div>
          </fieldset>
          {error && <p className="error">{error}</p>}
          <div className="modal-actions">
            <button
              type="button"
              className="danger-link"
              onClick={async () => {
                if (!confirm(t.deleteConfirm)) return;
                setBusy(true);
                try {
                  await onDelete();
                  onClose();
                } catch (err) {
                  setError(err instanceof Error ? err.message : t.deleteError);
                  setBusy(false);
                }
              }}
            >
              {t.deleteTask}
            </button>
            <span className="spacer" />
            <button type="button" className="secondary" onClick={onClose}>{t.cancel}</button>
            <button className="primary" disabled={busy}>
              {busy ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />}
              {t.saveChanges}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function ImportModal({
  file,
  preview,
  token,
  busy,
  language,
  onCancel,
  onConfirm,
}: {
  file: File;
  preview: Project;
  token: string;
  busy: boolean;
  language: Language;
  onCancel: () => void;
  onConfirm: (token: string) => void;
}) {
  const t = translations[language];
  return (
    <div className="modal-backdrop">
      <section className="modal import-modal" role="dialog" aria-modal="true">
        <div className="modal-head">
          <div><span className="eyebrow">{t.importPreview}</span><h2>{t.replacePlan}</h2></div>
          <button className="icon-button" onClick={onCancel} aria-label={t.close}><X size={19} /></button>
        </div>
        <div className="file-summary">
          <div className="file-icon"><FileSpreadsheet size={23} /></div>
          <div><strong>{file.name}</strong><span>{preview.tasks.length} {t.tasks} · {(file.size / 1024).toFixed(1)} KB</span></div>
          <span className="valid-badge"><Check size={13} /> {t.valid}</span>
        </div>
        <p className="muted">{t.importDescription}</p>
        <div className="preview-list">
          {preview.tasks.slice(0, 5).map((task) => (
            <div key={task.id}><span>{task.name}</span><small>{task.assignees.join(", ")} · {task.man_hours} h</small></div>
          ))}
          {preview.tasks.length > 5 && <div className="more">+ {preview.tasks.length - 5} {t.moreTasks}</div>}
        </div>
        <div className="modal-actions">
          <span className="spacer" />
          <button className="secondary" onClick={onCancel}>{t.cancel}</button>
          <button className="primary" onClick={() => onConfirm(token)} disabled={busy}>
            {busy ? <LoaderCircle className="spin" size={17} /> : <Upload size={17} />}
            {t.importPlan}
          </button>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [selected, setSelected] = useState<Task | null>(null);
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [input, setInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [error, setError] = useState("");
  const [importState, setImportState] = useState<{ file: File; token: string; project: Project } | null>(null);
  const [importBusy, setImportBusy] = useState(false);
  const [timelineScale, setTimelineScale] = useState<TimelineScale>("month");
  const [recentlyChangedIds, setRecentlyChangedIds] = useState<Set<string>>(new Set());
  const [language, setLanguage] = useState<Language>(() => localStorage.getItem("language") === "ru" ? "ru" : "en");
  const [assistantWidth, setAssistantWidth] = useState(360);
  const [agentModel, setAgentModel] = useState("qwen/qwen3.7-flash");
  const fileRef = useRef<HTMLInputElement>(null);
  const ganttApiRef = useRef<IApi | null>(null);
  const t = translations[language];

  useEffect(() => {
    api.project().then(setProject).catch((err) => setError(err.message));
    api.agentConfig().then((config) => setAgentModel(config.model)).catch(() => undefined);
  }, []);

  useEffect(() => {
    localStorage.setItem("language", language);
    document.documentElement.lang = language;
  }, [language]);

  const ganttTasks = useMemo(() => project?.tasks.map((task) => ({
    id: task.id,
    text: task.name,
    start: new Date(`${task.start_date}T00:00:00`),
    end: new Date(`${task.end_date}T00:00:00`),
    duration: task.duration,
    hours: task.man_hours,
    recentlyChanged: recentlyChangedIds.has(task.id),
    progress: 0,
  })) ?? [], [project, recentlyChangedIds]);

  const links = useMemo(() => project?.tasks.flatMap((task) => task.predecessor_ids.map((source, index) => ({
    id: `${task.id}-${source}-${index}`,
    source,
    target: task.id,
    type: "e2s" as const,
  }))) ?? [], [project]);

  const timelineConfig = useMemo(() => {
    const locale = language === "ru" ? "ru-RU" : "en-US";
    const monthLabel = (date: Date) => new Intl.DateTimeFormat(locale, {
      month: "short",
      year: "2-digit",
    }).format(date);
    return ({
      week: {
        scales: [
          { unit: "month", step: 1, format: monthLabel },
          { unit: "day", step: 1, format: (date: Date) => String(date.getDate()) },
        ],
        cellWidth: 42,
      },
      month: {
        scales: [
          { unit: "month", step: 1, format: monthLabel },
          { unit: "week", step: 1, format: (date: Date) => String(isoWeek(date)) },
        ],
        cellWidth: 52,
      },
      quarter: {
        scales: [
          { unit: "year", step: 1, format: (date: Date) => String(date.getFullYear()) },
          { unit: "month", step: 1, format: (date: Date) => new Intl.DateTimeFormat(locale, { month: "short" }).format(date) },
        ],
        cellWidth: 110,
      },
    } as const)[timelineScale];
  }, [language, timelineScale]);

  const initGantt = (ganttApi: IApi) => {
    ganttApiRef.current = ganttApi;
    ganttApi.on("select-task", ({ id }) => {
      const task = project?.tasks.find((item) => item.id === String(id));
      if (task) setSelected(task);
    });
  };

  const submitChat = async (text = input) => {
    if (!text.trim() || chatBusy) return;
    const history = messages
      .filter((item) => item.text.trim() && !item.streaming)
      .map((item) => ({ role: item.role, content: item.text }));
    setInput("");
    setMessages((items) => [...items, { role: "user", text }, { role: "assistant", text: "", streaming: true }]);
    setChatBusy(true);
    setError("");
    try {
      const result = await api.chat(text, history, (token) => {
        setMessages((items) => items.map((item, index) => index === items.length - 1 && item.streaming
          ? { ...item, text: item.text + token }
          : item));
      });
      setProject(result.project);
      setRecentlyChangedIds(new Set(result.changes.map((change) => change.task_id)));
      setMessages((items) => items.map((item, index) => index === items.length - 1 && item.streaming ? {
        role: "assistant", text: result.reply, changes: result.changes, usage: result.usage,
      } : item));
    } catch (err) {
      setMessages((items) => items.map((item, index) => index === items.length - 1 && item.streaming
        ? { role: "assistant", text: err instanceof Error ? err.message : t.requestError }
        : item));
    } finally {
      setChatBusy(false);
    }
  };

  const upload = async (file?: File) => {
    if (!file) return;
    setImportBusy(true);
    setError("");
    try {
      const result = await api.previewImport(file);
      setImportState({ file, ...result });
    } catch (err) {
      setError(err instanceof Error ? err.message : t.workbookError);
    } finally {
      setImportBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const startResize = (event: PointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = assistantWidth;
    const move = (moveEvent: globalThis.PointerEvent) => {
      setAssistantWidth(Math.min(620, Math.max(300, startWidth + startX - moveEvent.clientX)));
    };
    const stop = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
      document.body.classList.remove("resizing");
    };
    document.body.classList.add("resizing");
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop);
  };

  if (!project) {
    return <main className="loading-screen"><div className="brand-mark"><FlaskConical size={22} /></div><LoaderCircle className="spin" /><p>{error || t.loading}</p></main>;
  }

  const completion = project.tasks.reduce((last, task) => task.end_date > last ? task.end_date : last, project.start_date);
  const totalHours = project.tasks.reduce((total, task) => total + task.man_hours, 0);
  const team = [...new Set(project.tasks.flatMap((task) => task.assignees))];
  const ganttStart = new Date(`${project.start_date}T00:00:00`);
  const ganttEnd = new Date(`${completion}T00:00:00`);
  ganttEnd.setDate(ganttEnd.getDate() + 1);
  const TaskContent = ({ data }: { data: ITask }) => (
    <div className={`gantt-task-label${data.recentlyChanged ? " recently-changed-task" : ""}`}>
      {data.text}
    </div>
  );

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><div className="brand-mark"><FlaskConical size={19} /></div><span>BIOCAD Gantt chart</span><i>{t.demo}</i></div>
        <div className="top-actions">
          <div className="language-switch" aria-label="Language">
            {(["en", "ru"] as const).map((item) => <button key={item} className={language === item ? "active" : ""} onClick={() => setLanguage(item)}>{item.toUpperCase()}</button>)}
          </div>
          <input ref={fileRef} type="file" accept=".xlsx" hidden onChange={(event) => upload(event.target.files?.[0])} />
          <button className="secondary" onClick={() => fileRef.current?.click()} disabled={importBusy}>
            {importBusy ? <LoaderCircle className="spin" size={16} /> : <Upload size={16} />} {t.importExcel}
          </button>
          <a className="primary" href={api.exportUrl}><Download size={16} /> {t.export}</a>
          <button className="avatar" aria-label="User profile">NV</button>
        </div>
      </header>
      <main className="workspace" style={{ gridTemplateColumns: `minmax(0, 1fr) 8px ${assistantWidth}px` }}>
        <section className="plan-panel">
          <div className="panel-header">
            <div>
              <div className="title-line"><h1>{t.projectTimeline}</h1><span className="live-dot">{t.live}</span></div>
              <p>{project.tasks.length} {t.tasks} · {t.updated}</p>
            </div>
            <div className="view-actions">
              <button className="today-button" onClick={() => ganttApiRef.current?.exec("scroll-chart", { date: new Date() })}>{t.today}</button>
              <div className="segmented" aria-label="Timeline scale">
                {(["week", "month", "quarter"] as const).map((scale) => (
                  <button key={scale} className={timelineScale === scale ? "active" : ""} aria-pressed={timelineScale === scale} onClick={() => setTimelineScale(scale)}>{t[scale]}</button>
                ))}
              </div>
            </div>
          </div>
          <div className="summary-strip">
            <div><span>{t.startDate}</span><strong>{dateLabel(project.start_date, language)}</strong></div>
            <div><span>{t.targetCompletion}</span><strong>{dateLabel(completion, language)}</strong></div>
            <div className="hours-summary"><span>{t.totalManHours}</span><strong>{totalHours.toLocaleString(language === "ru" ? "ru-RU" : "en-US")} h</strong></div>
            <div><span>{t.team}</span><div className="avatar-stack">{team.slice(0, 5).map((name, index) => <i key={name} style={{ zIndex: 6 - index }} title={name}>{initials(name)}</i>)}</div></div>
          </div>
          <div className="gantt-wrap" key={`${project.revision}-${timelineScale}-${language}`}>
            <Willow>
              <Gantt
                tasks={ganttTasks}
                links={links}
                scales={[...timelineConfig.scales]}
                start={ganttStart}
                end={ganttEnd}
                autoScale={false}
                columns={[
                  { id: "text", header: t.task.toUpperCase(), width: 220 },
                  { id: "start", header: t.start.toUpperCase(), width: 95, align: "center" },
                  { id: "duration", header: t.days.toUpperCase(), width: 62, align: "center" },
                  { id: "hours", header: t.hours.toUpperCase(), width: 70, align: "center" },
                ]}
                cellHeight={48}
                cellWidth={timelineConfig.cellWidth}
                init={initGantt}
                taskTemplate={TaskContent}
              />
            </Willow>
          </div>
          <footer className="plan-footer"><span><i className="legend planned" /> {t.planned}</span><span><i className="legend changed" /> {t.recentlyChanged}</span><span className="hint">{t.selectHint}</span></footer>
        </section>
        <button
          className="resize-handle"
          onPointerDown={startResize}
          onKeyDown={(event) => {
            if (event.key === "ArrowLeft") setAssistantWidth((width) => Math.min(620, width + 20));
            if (event.key === "ArrowRight") setAssistantWidth((width) => Math.max(300, width - 20));
          }}
          aria-label={t.resizeAssistant}
          title={t.resizeAssistant}
        ><GripVertical size={15} /></button>
        <aside className="chat-panel">
          <div className="chat-head">
            <div className="ai-icon"><Sparkles size={17} /></div>
            <div className="agent-title"><h2>{t.assistant}</h2><p><i /> {t.agentReady}</p><code>{agentModel}</code></div>
            <div className="chat-head-actions">
              <button className="icon-button" title={t.clearChat} aria-label={t.clearChat} disabled={chatBusy || messages.length === 0} onClick={() => setMessages([])}><Trash2 size={17} /></button>
            </div>
          </div>
          <div className="messages">
            <div className="day-divider"><span>{t.today}</span></div>
            <div className="message-row assistant"><div className="bot-avatar"><Bot size={16} /></div><div className="bubble"><p>{t.welcome}</p></div></div>
            {messages.map((message, index) => (
              <div className={`message-row ${message.role}`} key={index}>
                {message.role === "assistant" && <div className="bot-avatar"><Bot size={16} /></div>}
                <div className="bubble">
                  {message.streaming && !message.text ? <div className="typing"><i /><i /><i /><span>{t.updating}</span></div> : <p>{message.text}{message.streaming && <span className="streaming-cursor" />}</p>}
                  {message.changes && <div className="changes">{message.changes.map((change) => <div key={change.task_id}><Check size={14} /><span><strong>{change.task_name}</strong><small>{change.description}</small></span></div>)}</div>}
                  {message.usage && <div className="usage-card" title={message.usage.model}>
                    <code>{t.model}: {message.usage.model}</code>
                    <span><strong>{message.usage.total_tokens.toLocaleString()}</strong> {t.tokenUsage}</span>
                    <small>{t.inputTokens}: {message.usage.prompt_tokens.toLocaleString()} · {t.outputTokens}: {message.usage.completion_tokens.toLocaleString()}</small>
                    <span><strong>${message.usage.cost_usd.toFixed(6)}</strong> {t.runCost}</span>
                  </div>}
                </div>
              </div>
            ))}
            {messages.length === 0 && <div className="suggestions"><span>{t.tryCommand}</span>{examples[language].map((example) => <button key={example} onClick={() => submitChat(example)}>{example}<Send size={13} /></button>)}</div>}
          </div>
          <form className="composer" onSubmit={(event) => { event.preventDefault(); submitChat(); }}>
            <textarea rows={3} placeholder={t.askPlaceholder} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submitChat(); } }} />
            <div><span>{t.sendHint}</span><button disabled={!input.trim() || chatBusy} aria-label={t.send}><Send size={17} /></button></div>
          </form>
        </aside>
      </main>
      {selected && <TaskModal task={selected} project={project} language={language} onClose={() => setSelected(null)} onSave={async (body) => { setProject(await api.updateTask(selected.id, body)); setRecentlyChangedIds(new Set([selected.id])); }} onDelete={async () => { setProject(await api.deleteTask(selected.id)); setRecentlyChangedIds(new Set()); }} />}
      {importState && <ImportModal file={importState.file} token={importState.token} preview={importState.project} busy={importBusy} language={language} onCancel={() => setImportState(null)} onConfirm={async (token) => {
        setImportBusy(true);
        try {
          setProject(await api.confirmImport(token));
          setRecentlyChangedIds(new Set());
          setImportState(null);
          setMessages((items) => [...items, { role: "assistant", text: t.importSuccess }]);
        } catch (err) {
          setError(err instanceof Error ? err.message : t.importFailed);
        } finally {
          setImportBusy(false);
        }
      }} />}
      {error && <button className="toast" onClick={() => setError("")}><X size={15} />{error}</button>}
    </div>
  );
}
