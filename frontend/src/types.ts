export interface Task {id:string;name:string;description:string;assignee:string;duration:number;predecessor_ids:string[];start_offset:number;start_date:string;end_date:string}
export interface Project {id:string;name:string;start_date:string;tasks:Task[];revision:number}
export interface Change {task_id:string;task_name:string;description:string}
export interface ChatResponse {reply:string;changes:Change[];project:Project;can_undo:boolean}
