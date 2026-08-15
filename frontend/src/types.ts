export type Person = "Elena" | "Mikhail" | "Daria" | "Anna" | "Pavel";

export interface Task {
  id: string;
  name: string;
  description: string;
  assignees: Person[];
  duration: number;
  man_hours: number;
  predecessor_ids: string[];
  start_offset: number;
  start_date: string;
  end_date: string;
}

export interface Project {
  id: string;
  name: string;
  start_date: string;
  tasks: Task[];
  team: Person[];
  revision: number;
}

export interface Change {
  task_id: string;
  task_name: string;
  description: string;
}

export interface ChatResponse {
  reply: string;
  changes: Change[];
  project: Project;
  can_undo: boolean;
  usage: AgentUsage;
}

export interface AgentUsage {
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
}
