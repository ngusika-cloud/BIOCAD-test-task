import type { ChatResponse, Project } from "./types";
const API = import.meta.env.VITE_API_URL ?? "";
export type ChatHistoryItem = {role:"user"|"assistant";content:string};
async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {const body = await response.json().catch(() => ({detail:"Something went wrong"}));throw new Error(body.detail ?? "Something went wrong");}
  return response.json() as Promise<T>;
}
async function streamChat(message:string, history:ChatHistoryItem[], onToken:(token:string)=>void):Promise<ChatResponse> {
  const response = await fetch(API + "/api/chat/stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message,history})});
  if (!response.ok) return parse<ChatResponse>(response);
  if (!response.body) throw new Error("Streaming is not supported by this browser");
  const reader=response.body.getReader();const decoder=new TextDecoder();let buffer="";let result:ChatResponse|undefined;
  const handle=(block:string) => {
    let event="message";const data:string[]=[];
    for (const line of block.split("\n")) {if(line.startsWith("event:")) event=line.slice(6).trim();if(line.startsWith("data:")) data.push(line.slice(5).trim());}
    if (!data.length) return;
    const payload=JSON.parse(data.join("\n"));
    if(event==="token") onToken(payload.text);
    if(event==="result") result=payload as ChatResponse;
    if(event==="error") throw new Error(payload.detail ?? "AI request failed");
  };
  while(true){const {done,value}=await reader.read();buffer+=decoder.decode(value,{stream:!done}).replace(/\r\n/g,"\n");let boundary=buffer.indexOf("\n\n");while(boundary>=0){handle(buffer.slice(0,boundary));buffer=buffer.slice(boundary+2);boundary=buffer.indexOf("\n\n");}if(done)break;}
  if(buffer.trim())handle(buffer);
  if(!result)throw new Error("The AI stream ended without a result");
  return result;
}
export const api = {
  project: () => fetch(API + "/api/project").then(parse<Project>),
  updateTask: (id:string, body:object) => fetch(API + "/api/tasks/" + id,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(parse<Project>),
  deleteTask: (id:string) => fetch(API + "/api/tasks/" + id,{method:"DELETE"}).then(parse<Project>),
  chat: streamChat,
  agentConfig: () => fetch(API + "/api/agent/config").then(parse<{model:string}>),
  undo: () => fetch(API + "/api/project/undo",{method:"POST"}).then(parse<Project>),
  reset: () => fetch(API + "/api/project/reset",{method:"POST"}).then(parse<Project>),
  previewImport: (file:File) => {const data=new FormData();data.append("file",file);return fetch(API + "/api/import/preview",{method:"POST",body:data}).then(parse<{token:string;project:Project}>);},
  confirmImport: (token:string) => fetch(API + "/api/import/" + token + "/confirm",{method:"POST"}).then(parse<Project>),
  exportUrl: API + "/api/export",
};
