import { useState, useEffect } from "react";
import {
  startWorkflow,
  resetWorkflow,
  setWeights,
  submitTasks,
  setConstraints,
  generateSchedule,
  APIError,
} from "./api";
import type { WorkflowState, UtilityWeights, TaskWithConstraints, CategorisedTask } from "./api";
import { WeightsForm } from "./components/WeightsForm";
import { TaskInput } from "./components/TaskInput";
import { ConstraintForm } from "./components/ConstraintForm";
import { ScheduleReady } from "./components/ScheduleReady";
import { CalendarView } from "./components/CalendarView";

function App() {
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [state, setState] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [message, setMessage] = useState<string>("");

  // Initialize workflow on mount
  useEffect(() => {
    initWorkflow();
  }, []);

  const handleAPIError = (err: unknown, fallbackMessage: string) => {
    if (err instanceof APIError) {
      setError(err.detail);
    } else if (err instanceof Error) {
      setError(err.message);
    } else {
      setError(fallbackMessage);
    }
  };

  const initWorkflow = async () => {
    setLoading(true);
    setError(null);
    setWarnings([]);
    try {
      const response = await startWorkflow(sessionId);
      setState(response.state);
      setMessage(response.message);
      setWarnings(response.warnings || []);
    } catch (err) {
      handleAPIError(err, "Failed to start workflow");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    setError(null);
    setWarnings([]);
    try {
      const response = await resetWorkflow(sessionId);
      setState(response.state);
      setMessage(response.message);
      setWarnings(response.warnings || []);
    } catch (err) {
      handleAPIError(err, "Failed to reset workflow");
    } finally {
      setLoading(false);
    }
  };

  const handleSetWeights = async (weights: UtilityWeights) => {
    setLoading(true);
    setError(null);
    setWarnings([]);
    try {
      const response = await setWeights(sessionId, weights);
      setState(response.state);
      setMessage(response.message);
      setWarnings(response.warnings || []);
    } catch (err) {
      handleAPIError(err, "Failed to set weights");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitTasks = async (tasks: string[]) => {
    setLoading(true);
    setError(null);
    setWarnings([]);
    try {
      const response = await submitTasks(sessionId, tasks);
      setState(response.state);
      setMessage(response.message);
      setWarnings(response.warnings || []);
    } catch (err) {
      handleAPIError(err, "Failed to submit tasks");
    } finally {
      setLoading(false);
    }
  };

  const handleSetConstraints = async (
    tasks: TaskWithConstraints[],
    windowStart: string,
    windowEnd: string
  ) => {
    setLoading(true);
    setError(null);
    setWarnings([]);
    try {
      const response = await setConstraints(sessionId, tasks, windowStart, windowEnd);
      setState(response.state);
      setMessage(response.message);
      setWarnings(response.warnings || []);
    } catch (err) {
      handleAPIError(err, "Failed to set constraints");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSchedule = async () => {
    setLoading(true);
    setError(null);
    setWarnings([]);
    try {
      const response = await generateSchedule(sessionId);
      setState(response.state);
      setMessage(response.message);
      setWarnings(response.warnings || []);
    } catch (err) {
      handleAPIError(err, "Failed to generate schedule");
    } finally {
      setLoading(false);
    }
  };

  const phaseLabels: Record<string, string> = {
    weights: "1. Set Weights",
    tasks: "2. Enter Tasks",
    constraints: "3. Set Constraints",
    schedule: "4. Generate",
    complete: "Complete",
  };

  const phases = ["weights", "tasks", "constraints", "schedule", "complete"];
  const currentPhaseIndex = state ? phases.indexOf(state.phase) : 0;

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <h1>Daily Schedule Planner</h1>

      {/* Progress indicator */}
      {state && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
            {phases.slice(0, -1).map((phase, i) => (
              <div
                key={phase}
                style={{
                  flex: 1,
                  padding: 8,
                  textAlign: "center",
                  backgroundColor: i <= currentPhaseIndex ? "#2196F3" : "#e0e0e0",
                  color: i <= currentPhaseIndex ? "white" : "#666",
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: i === currentPhaseIndex ? "bold" : "normal",
                }}
              >
                {phaseLabels[phase]}
              </div>
            ))}
          </div>
          {message && (
            <div style={{ fontSize: 14, color: "#666", textAlign: "center" }}>
              {message}
            </div>
          )}
        </div>
      )}

      {/* Loading overlay */}
      {loading && (
        <div
          style={{
            padding: 16,
            marginBottom: 16,
            backgroundColor: "#e3f2fd",
            borderRadius: 4,
            textAlign: "center",
          }}
        >
          <div style={{ display: "inline-block", marginRight: 8 }}>
            <div
              style={{
                width: 16,
                height: 16,
                border: "2px solid #2196F3",
                borderTopColor: "transparent",
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
              }}
            />
          </div>
          Processing...
          <style>{`
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div
          style={{
            color: "#c62828",
            padding: 12,
            marginBottom: 16,
            backgroundColor: "#ffebee",
            borderRadius: 4,
            borderLeft: "4px solid #c62828",
          }}
        >
          <strong>Error:</strong> {error}
          <button
            onClick={() => setError(null)}
            style={{
              float: "right",
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: 16,
              color: "#c62828",
            }}
          >
            ×
          </button>
        </div>
      )}

      {/* Warnings display */}
      {warnings.length > 0 && (
        <div
          style={{
            color: "#e65100",
            padding: 12,
            marginBottom: 16,
            backgroundColor: "#fff3e0",
            borderRadius: 4,
            borderLeft: "4px solid #FF9800",
          }}
        >
          <strong>Warnings:</strong>
          <ul style={{ margin: "8px 0 0 0", paddingLeft: 20 }}>
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Schedule warnings from state */}
      {state?.schedule_warnings && state.schedule_warnings.length > 0 && (
        <div
          style={{
            color: "#e65100",
            padding: 12,
            marginBottom: 16,
            backgroundColor: "#fff3e0",
            borderRadius: 4,
            borderLeft: "4px solid #FF9800",
          }}
        >
          <strong>Schedule Notes:</strong>
          <ul style={{ margin: "8px 0 0 0", paddingLeft: 20 }}>
            {state.schedule_warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Phase content */}
      {state?.phase === "weights" && !loading && (
        <WeightsForm onSubmit={handleSetWeights} loading={loading} />
      )}

      {state?.phase === "tasks" && !loading && (
        <TaskInput onSubmit={handleSubmitTasks} loading={loading} />
      )}

      {state?.phase === "constraints" && state.categorised_tasks && !loading && (
        <ConstraintForm
          categorisedTasks={state.categorised_tasks as CategorisedTask[]}
          onSubmit={handleSetConstraints}
          loading={loading}
        />
      )}

      {state?.phase === "schedule" && !loading && (
        <ScheduleReady onGenerate={handleGenerateSchedule} loading={loading} />
      )}

      {state?.phase === "complete" && state.schedule && state.window_start && state.window_end && (
        <CalendarView
          schedule={state.schedule}
          windowStart={state.window_start}
          windowEnd={state.window_end}
          algorithm={state.selected_algorithm}
        />
      )}

      {/* Reset button */}
      {state && state.phase !== "weights" && (
        <button
          onClick={handleReset}
          disabled={loading}
          style={{
            marginTop: 24,
            padding: "8px 16px",
            cursor: loading ? "wait" : "pointer",
            backgroundColor: "#f5f5f5",
            border: "1px solid #ddd",
            borderRadius: 4,
            opacity: loading ? 0.6 : 1,
          }}
        >
          Start Over
        </button>
      )}

      {/* Debug: Show current state */}
      {state && (
        <details style={{ marginTop: 40, fontSize: 12, color: "#666" }}>
          <summary style={{ cursor: "pointer" }}>Debug: Workflow State (JSON)</summary>
          <pre
            style={{
              marginTop: 8,
              padding: 12,
              backgroundColor: "#f5f5f5",
              borderRadius: 4,
              overflow: "auto",
            }}
          >
            {JSON.stringify(state, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

export default App;
