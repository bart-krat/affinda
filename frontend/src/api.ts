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
  error: string | null;
  weights: UtilityWeights | null;
  raw_tasks: string[] | null;
  categorised_tasks: CategorisedTask[] | null;
  tasks_with_constraints: TaskWithConstraints[] | null;
  window_start: string | null;
  window_end: string | null;
  selected_algorithm: string | null;
  schedule: ScheduledBlock[] | null;
  schedule_warnings: string[] | null;
}

export interface WorkflowResponse {
  state: WorkflowState;
  message: string;
  warnings: string[];
}

export class APIError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "APIError";
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse(response: Response): Promise<WorkflowResponse> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      // Ignore JSON parse errors
    }

    if (response.status === 503) {
      throw new APIError(response.status, "Service temporarily unavailable. Please try again.");
    } else if (response.status === 422) {
      throw new APIError(response.status, `Validation error: ${detail}`);
    } else if (response.status === 400) {
      throw new APIError(response.status, detail);
    } else if (response.status === 404) {
      throw new APIError(response.status, "Session not found. Please start over.");
    } else {
      throw new APIError(response.status, `Server error: ${detail}`);
    }
  }
  return response.json();
}

// API Functions
export async function startWorkflow(sessionId: string): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/start?session_id=${encodeURIComponent(sessionId)}`, {
    method: "POST",
  });
  return handleResponse(response);
}

export async function getWorkflowState(sessionId: string): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/state/${encodeURIComponent(sessionId)}`);
  return handleResponse(response);
}

export async function resetWorkflow(sessionId: string): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/reset/${encodeURIComponent(sessionId)}`, {
    method: "POST",
  });
  return handleResponse(response);
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
  return handleResponse(response);
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
  return handleResponse(response);
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
  return handleResponse(response);
}

export async function generateSchedule(sessionId: string): Promise<WorkflowResponse> {
  const response = await fetch(`${API_BASE}/workflow/phase4/schedule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return handleResponse(response);
}
