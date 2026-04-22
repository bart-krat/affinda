const API_BASE = "http://localhost:8000";

// Types
export type WorkflowPhase = "weights" | "tasks" | "constraints" | "schedule" | "complete";

export interface UtilityWeights {
  personal: number;
  health: number;
  work: number;
}

export interface CategorisedTask {
  description: string;
  category: "Personal" | "Health" | "Work";
}

export interface TaskWithConstraints {
  id: string;
  description: string;
  category: string;
  duration_minutes: number;
  fixed_start_time: string | null;
}

export interface ScheduledBlock {
  task_id: string;
  description: string;
  category: string;
  start_time: string;
  end_time: string;
}

export interface WorkflowState {
  session_id: string;
  phase: WorkflowPhase;
  weights: UtilityWeights | null;
  raw_tasks: string[] | null;
  categorised_tasks: CategorisedTask[] | null;
  tasks_with_constraints: TaskWithConstraints[] | null;
  window_start: string | null;
  window_end: string | null;
  selected_algorithm: string | null;
  schedule: ScheduledBlock[] | null;
}

export interface WorkflowResponse {
  state: WorkflowState;
  message: string;
}

// API Functions
export async function startWorkflow(sessionId: string): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/start?session_id=${sessionId}`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function getWorkflowState(sessionId: string): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/state/${sessionId}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function resetWorkflow(sessionId: string): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/reset/${sessionId}`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function setWeights(
  sessionId: string,
  weights: UtilityWeights
): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/phase1/weights`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, weights }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function submitTasks(
  sessionId: string,
  tasks: string[]
): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/phase2/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, tasks }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function setConstraints(
  sessionId: string,
  tasks: TaskWithConstraints[],
  windowStart: string,
  windowEnd: string
): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/phase3/constraints`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      tasks,
      window_start: windowStart,
      window_end: windowEnd,
    }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function generateSchedule(sessionId: string): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/phase4/schedule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}
