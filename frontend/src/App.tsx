import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Gantt, Willow, type IApi } from "@svar-ui/react-gantt";
import "@svar-ui/react-gantt/all.css";
import { ArrowDownToLine, Bot, CalendarDays, Check, ChevronDown, Clock3, Download, FileSpreadsheet, FlaskConical, LoaderCircle, RotateCcw, Send, Sparkles, Upload, UserRound, X } from "lucide-react";
import { api } from "./api";
import type { Change, Project, Task } from "./types";

type ChatItem = {role:"assistant"|"user"; text:string; changes?:Change[]};
type TimelineScale = "week" | "month" | "quarter";
const examples = ["Assign Hit analysis to Elena","Move Primary screening by 3 days","Add a 3-day QA task after Lead selection","Move all of Anna's tasks by one week"];

function dateLabel(value:string) {
  return new Intl.DateTimeFormat("en-US",{month:"short",day:"numeric",year:"numeric",timeZone:"UTC"}).format(new Date(value+"T00:00:00Z"));
}
function initials(name:string) {return name.split(/\s+/).map(part=>part[0]).join("").slice(0,2).toUpperCase();}

function TaskModal({task,project,onClose,onSave,onDelete}:{task:Task;project:Project;onClose:()=>void;onSave:(body:object)=>Promise<void>;onDelete:()=>Promise<void>}) {
  const [form,setForm]=useState({...task});
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const submit=async(e:FormEvent)=>{
    e.preventDefault();setBusy(true);setError("");
    try {await onSave({name:form.name,description:form.description,assignee:form.assignee,duration:Number(form.duration),predecessor_ids:form.predecessor_ids});onClose();}
    catch(err){setError(err instanceof Error?err.message:"Could not save task");}
    finally{setBusy(false);}
  };
  return <div className="modal-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="task-title">
      <div className="modal-head"><div><span className="eyebrow">Task details</span><h2 id="task-title">{task.name}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close"><X size={19}/></button></div>
      <form onSubmit={submit}>
        <label>Task name<input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required/></label>
        <label>Description<textarea rows={4} value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label>
        <div className="form-grid">
          <label>Assignee<input value={form.assignee} onChange={e=>setForm({...form,assignee:e.target.value})} required/></label>
          <label>Duration (days)<input type="number" min="1" max="365" value={form.duration} onChange={e=>setForm({...form,duration:Number(e.target.value)})}/></label>
        </div>
        <div className="date-card"><CalendarDays size={17}/><div><span>Scheduled window</span><strong>{dateLabel(task.start_date)} — {dateLabel(task.end_date)}</strong></div></div>
        <fieldset><legend>Predecessors</legend><div className="check-list">{project.tasks.filter(item=>item.id!==task.id).map(item=><label className="check-row" key={item.id}><input type="checkbox" checked={form.predecessor_ids.includes(item.id)} onChange={e=>setForm({...form,predecessor_ids:e.target.checked?[...form.predecessor_ids,item.id]:form.predecessor_ids.filter(id=>id!==item.id)})}/><span>{item.name}</span></label>)}</div></fieldset>
        {error&&<p className="error">{error}</p>}
        <div className="modal-actions"><button type="button" className="danger-link" onClick={async()=>{if(confirm("Delete this task?")){setBusy(true);try{await onDelete();onClose();}catch(err){setError(err instanceof Error?err.message:"Could not delete");setBusy(false);}}}}>Delete task</button><span className="spacer"/><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="primary" disabled={busy}>{busy?<LoaderCircle className="spin" size={17}/>:<Check size={17}/>} Save changes</button></div>
      </form>
    </section>
  </div>;
}
function ImportModal({file,preview,token,busy,onCancel,onConfirm}:{file:File;preview:Project;token:string;busy:boolean;onCancel:()=>void;onConfirm:(token:string)=>void}) {
  return <div className="modal-backdrop"><section className="modal import-modal" role="dialog" aria-modal="true">
    <div className="modal-head"><div><span className="eyebrow">Import preview</span><h2>Replace current plan?</h2></div><button className="icon-button" onClick={onCancel}><X size={19}/></button></div>
    <div className="file-summary"><div className="file-icon"><FileSpreadsheet size={23}/></div><div><strong>{file.name}</strong><span>{preview.tasks.length} tasks · {(file.size/1024).toFixed(1)} KB</span></div><span className="valid-badge"><Check size={13}/> Valid</span></div>
    <p className="muted">The workbook passed column, duration, predecessor, and cycle validation. Confirming will replace the current plan; you can undo it afterward.</p>
    <div className="preview-list">{preview.tasks.slice(0,5).map(task=><div key={task.id}><span>{task.name}</span><small>{task.assignee} · {task.duration}d</small></div>)}{preview.tasks.length>5&&<div className="more">+ {preview.tasks.length-5} more tasks</div>}</div>
    <div className="modal-actions"><span className="spacer"/><button className="secondary" onClick={onCancel}>Cancel</button><button className="primary" onClick={()=>onConfirm(token)} disabled={busy}>{busy?<LoaderCircle className="spin" size={17}/>:<Upload size={17}/>} Import plan</button></div>
  </section></div>;
}

export default function App() {
  const [project,setProject]=useState<Project|null>(null);
  const [selected,setSelected]=useState<Task|null>(null);
  const [messages,setMessages]=useState<ChatItem[]>([{role:"assistant",text:"I’m your planning copilot. Tell me what to change and I’ll update the schedule instantly."}]);
  const [input,setInput]=useState("");
  const [chatBusy,setChatBusy]=useState(false);
  const [error,setError]=useState("");
  const [canUndo,setCanUndo]=useState(false);
  const [importState,setImportState]=useState<{file:File;token:string;project:Project}|null>(null);
  const [importBusy,setImportBusy]=useState(false);
  const [timelineScale,setTimelineScale]=useState<TimelineScale>("month");
  const fileRef=useRef<HTMLInputElement>(null);

  useEffect(()=>{api.project().then(setProject).catch(err=>setError(err.message));},[]);
  const ganttTasks=useMemo(()=>project?.tasks.map(task=>({id:task.id,text:task.name,start:new Date(task.start_date+"T00:00:00"),end:new Date(task.end_date+"T00:00:00"),duration:task.duration,progress:0}))??[],[project]);
  const links=useMemo(()=>project?.tasks.flatMap(task=>task.predecessor_ids.map((source,index)=>({id:task.id+"-"+source+"-"+index,source,target:task.id,type:"e2s" as const})))??[],[project]);
  const timelineConfig=useMemo(()=>({
    week:{scales:[{unit:"month",step:1,format:"%F %Y"},{unit:"day",step:1,format:"%d %M"}],cellWidth:42},
    month:{scales:[{unit:"month",step:1,format:"%F %Y"},{unit:"week",step:1,format:"Week %w"}],cellWidth:52},
    quarter:{scales:[{unit:"year",step:1,format:"%Y"},{unit:"month",step:1,format:"%F"}],cellWidth:110},
  } as const)[timelineScale],[timelineScale]);
  const initGantt=(ganttApi:IApi)=>{ganttApi.on("select-task",({id})=>{const task=project?.tasks.find(item=>item.id===String(id));if(task)setSelected(task);});};
  const submitChat=async(text=input)=>{
    if(!text.trim()||chatBusy)return;
    setInput("");setMessages(items=>[...items,{role:"user",text}]);setChatBusy(true);setError("");
    try{const result=await api.chat(text);setProject(result.project);setCanUndo(result.can_undo);setMessages(items=>[...items,{role:"assistant",text:result.reply,changes:result.changes}]);}
    catch(err){setMessages(items=>[...items,{role:"assistant",text:err instanceof Error?err.message:"I couldn't apply that change."}]);}
    finally{setChatBusy(false);}
  };
  const undo=async()=>{try{const result=await api.undo();setProject(result);setCanUndo(false);setMessages(items=>[...items,{role:"assistant",text:"The last plan change has been undone."}]);}catch(err){setError(err instanceof Error?err.message:"Could not undo");}};
  const upload=async(file?:File)=>{if(!file)return;setImportBusy(true);setError("");try{const result=await api.previewImport(file);setImportState({file,...result});}catch(err){setError(err instanceof Error?err.message:"Could not read workbook");}finally{setImportBusy(false);if(fileRef.current)fileRef.current.value="";}};
  if(!project)return <main className="loading-screen"><div className="brand-mark"><FlaskConical size={22}/></div><LoaderCircle className="spin"/><p>{error||"Loading your plan…"}</p></main>;

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand"><div className="brand-mark"><FlaskConical size={19}/></div><span>PlanPilot</span><i>Demo</i></div>
      <div className="project-switch"><div><span>Workspace</span><strong>{project.name}</strong></div><ChevronDown size={16}/></div>
      <div className="top-actions">
        <input ref={fileRef} type="file" accept=".xlsx" hidden onChange={e=>upload(e.target.files?.[0])}/>
        <button className="secondary" onClick={()=>fileRef.current?.click()} disabled={importBusy}>{importBusy?<LoaderCircle className="spin" size={16}/>:<Upload size={16}/>} Import Excel</button>
        <a className="primary" href={api.exportUrl}><Download size={16}/> Export</a>
        <button className="avatar" aria-label="User profile">NV</button>
      </div>
    </header>
    <main className="workspace">
      <section className="plan-panel">
        <div className="panel-header">
          <div><div className="title-line"><h1>Project timeline</h1><span className="live-dot">Live</span></div><p>{project.tasks.length} tasks · Updated just now</p></div>
          <div className="view-actions"><button className="ghost" onClick={undo} disabled={!canUndo}><RotateCcw size={15}/> Undo</button><button className="today-button">Today</button><div className="segmented" aria-label="Timeline scale">{(["week","month","quarter"] as const).map(scale=><button key={scale} className={timelineScale===scale?"active":""} aria-pressed={timelineScale===scale} onClick={()=>setTimelineScale(scale)}>{scale[0].toUpperCase()+scale.slice(1)}</button>)}</div></div>
        </div>
        <div className="summary-strip">
          <div><span>Start date</span><strong>{dateLabel(project.start_date)}</strong></div>
          <div><span>Target completion</span><strong>{dateLabel(project.tasks.reduce((last,task)=>task.end_date>last?task.end_date:last,project.start_date))}</strong></div>
          <div><span>Team</span><div className="avatar-stack">{[...new Set(project.tasks.map(task=>task.assignee))].slice(0,4).map((name,index)=><i key={name} style={{zIndex:5-index}} title={name}>{initials(name)}</i>)}</div></div>
        </div>
        <div className="gantt-wrap" key={project.revision+"-"+timelineScale}><Willow><Gantt tasks={ganttTasks} links={links} scales={[...timelineConfig.scales]} columns={[{id:"text",header:"TASK",width:230},{id:"start",header:"START",width:100,align:"center"},{id:"duration",header:"DAYS",width:68,align:"center"}]} cellHeight={48} cellWidth={timelineConfig.cellWidth} init={initGantt}/></Willow></div>
        <footer className="plan-footer"><span><i className="legend planned"/> Planned</span><span><i className="legend changed"/> Recently changed</span><span className="hint">Select any task to view and edit details</span></footer>
      </section>
      <aside className="chat-panel">
        <div className="chat-head"><div className="ai-icon"><Sparkles size={17}/></div><div><h2>Planning assistant</h2><p><i/> Mock mode · Ready</p></div><button className="icon-button" title="Reset seed" onClick={async()=>{setProject(await api.reset());setCanUndo(true);}}><RotateCcw size={17}/></button></div>
        <div className="messages">
          <div className="day-divider"><span>Today</span></div>
          {messages.map((message,index)=><div className={"message-row "+message.role} key={index}>{message.role==="assistant"&&<div className="bot-avatar"><Bot size={16}/></div>}<div className="bubble"><p>{message.text}</p>{message.changes&&<div className="changes">{message.changes.map(change=><div key={change.task_id}><Check size={14}/><span><strong>{change.task_name}</strong><small>{change.description}</small></span></div>)}</div>}</div></div>)}
          {messages.length===1&&<div className="suggestions"><span>Try a command</span>{examples.map(example=><button key={example} onClick={()=>submitChat(example)}>{example}<Send size={13}/></button>)}</div>}
          {chatBusy&&<div className="message-row assistant"><div className="bot-avatar"><Bot size={16}/></div><div className="bubble typing"><i/><i/><i/><span>Updating project…</span></div></div>}
        </div>
        {canUndo&&<button className="undo-banner" onClick={undo}><RotateCcw size={15}/><span><strong>Last change applied</strong>Undo the latest update</span></button>}
        <form className="composer" onSubmit={e=>{e.preventDefault();submitChat();}}><textarea rows={3} placeholder="Ask me to update the plan…" value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();submitChat();}}}/><div><span>Enter to send · Shift + Enter for new line</span><button disabled={!input.trim()||chatBusy} aria-label="Send"><Send size={17}/></button></div></form>
      </aside>
    </main>
    {selected&&<TaskModal task={selected} project={project} onClose={()=>setSelected(null)} onSave={async body=>setProject(await api.updateTask(selected.id,body))} onDelete={async()=>setProject(await api.deleteTask(selected.id))}/>}
    {importState&&<ImportModal file={importState.file} token={importState.token} preview={importState.project} busy={importBusy} onCancel={()=>setImportState(null)} onConfirm={async token=>{setImportBusy(true);try{setProject(await api.confirmImport(token));setCanUndo(true);setImportState(null);setMessages(items=>[...items,{role:"assistant",text:"Excel imported successfully. The new plan is ready."}]);}catch(err){setError(err instanceof Error?err.message:"Import failed");}finally{setImportBusy(false);}}}/>}
    {error&&<button className="toast" onClick={()=>setError("")}><X size={15}/>{error}</button>}
  </div>;
}

