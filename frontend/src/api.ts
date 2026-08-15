import type { ChatResponse, Project } from "./types";
const API = import.meta.env.VITE_API_URL ?? "";
async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {const body = await response.json().catch(() => ({detail:"Something went wrong"}));throw new Error(body.detail ?? "Something went wrong");}
  return response.json() as Promise<T>;
}
export const api = {
  project: () => fetch(API + "/api/project").then(parse<Project>),
  updateTask: (id:string, body:object) => fetch(API + "/api/tasks/" + id,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(parse<Project>),
  deleteTask: (id:string) => fetch(API + "/api/tasks/" + id,{method:"DELETE"}).then(parse<Project>),
  chat: (message:string) => fetch(API + "/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message})}).then(parse<ChatResponse>),
  undo: () => fetch(API + "/api/project/undo",{method:"POST"}).then(parse<Project>),
  reset: () => fetch(API + "/api/project/reset",{method:"POST"}).then(parse<Project>),
  previewImport: (file:File) => {const data=new FormData();data.append("file",file);return fetch(API + "/api/import/preview",{method:"POST",body:data}).then(parse<{token:string;project:Project}>);},
  confirmImport: (token:string) => fetch(API + "/api/import/" + token + "/confirm",{method:"POST"}).then(parse<Project>),
  exportUrl: API + "/api/export",
};
