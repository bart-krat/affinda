import { useState } from "react";
import type { CategorisedTask, TaskWithConstraints } from "../api";

interface Props {
  categorisedTasks: CategorisedTask[];
  onSubmit: (tasks: TaskWithConstraints[], windowStart: string, windowEnd: string) => void;
  loading: boolean;
}

export function ConstraintForm({ categorisedTasks, onSubmit, loading }: Props) {
  const [durations, setDurations] = useState<Record<number, number>>(() =>
    Object.fromEntries(categorisedTasks.map((_, i) => [i, 30]))
  );
  const [fixedTimes, setFixedTimes] = useState<Record<number, string>>({});
  const [windowStart, setWindowStart] = useState("08:00");
  const [windowEnd, setWindowEnd] = useState("18:00");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const tasks: TaskWithConstraints[] = categorisedTasks.map((task, i) => ({
      id: `task-${i}`,
      description: task.description,
      category: task.category,
      duration_minutes: durations[i] || 30,
      fixed_start_time: fixedTimes[i] || null,
    }));
    onSubmit(tasks, windowStart, windowEnd);
  };

  const categoryColor = (category: string) => {
    switch (category) {
      case "Personal":
        return "#4CAF50";
      case "Health":
        return "#2196F3";
      case "Work":
        return "#FF9800";
      default:
        return "#9E9E9E";
    }
  };

  // Calculate total duration
  const totalDuration = Object.values(durations).reduce((sum, d) => sum + d, 0);
  const windowMinutes = (() => {
    const [startH, startM] = windowStart.split(":").map(Number);
    const [endH, endM] = windowEnd.split(":").map(Number);
    return (endH * 60 + endM) - (startH * 60 + startM);
  })();
  const fitsInWindow = totalDuration <= windowMinutes;

  return (
    <form onSubmit={handleSubmit}>
      <h2>Step 3: Set Time Constraints</h2>

      <div style={{ marginBottom: 24, padding: 16, backgroundColor: "#f0f0f0", borderRadius: 8 }}>
        <h3 style={{ marginTop: 0 }}>Day Window</h3>
        <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            Start:
            <input
              type="time"
              value={windowStart}
              onChange={(e) => setWindowStart(e.target.value)}
            />
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            End:
            <input
              type="time"
              value={windowEnd}
              onChange={(e) => setWindowEnd(e.target.value)}
            />
          </label>
          <span style={{ color: "#666" }}>
            ({Math.floor(windowMinutes / 60)}h {windowMinutes % 60}m available)
          </span>
        </div>
      </div>

      <div
        style={{
          marginBottom: 16,
          padding: 12,
          backgroundColor: fitsInWindow ? "#e8f5e9" : "#fff3e0",
          borderRadius: 4,
          borderLeft: `4px solid ${fitsInWindow ? "#4CAF50" : "#FF9800"}`,
        }}
      >
        <strong>Total task time: </strong>
        {Math.floor(totalDuration / 60)}h {totalDuration % 60}m
        {!fitsInWindow && (
          <span style={{ color: "#e65100" }}>
            {" "}— exceeds window, optimizer will prioritize by weight
          </span>
        )}
      </div>

      <h3>Task Durations & Fixed Times</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {categorisedTasks.map((task, i) => (
          <div
            key={i}
            style={{
              padding: 12,
              backgroundColor: "#f5f5f5",
              borderLeft: `4px solid ${categoryColor(task.category)}`,
              borderRadius: 4,
            }}
          >
            <div style={{ marginBottom: 8 }}>
              <strong>{task.description}</strong>
              <span
                style={{
                  marginLeft: 10,
                  padding: "2px 8px",
                  borderRadius: 4,
                  backgroundColor: categoryColor(task.category),
                  color: "white",
                  fontSize: 12,
                }}
              >
                {task.category}
              </span>
            </div>
            <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                Duration:
                <input
                  type="number"
                  min="5"
                  max="480"
                  step="5"
                  value={durations[i] || 30}
                  onChange={(e) =>
                    setDurations({ ...durations, [i]: parseInt(e.target.value) || 30 })
                  }
                  style={{ width: 60 }}
                />
                <span>min</span>
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                Fixed start:
                <input
                  type="time"
                  value={fixedTimes[i] || ""}
                  onChange={(e) =>
                    setFixedTimes({ ...fixedTimes, [i]: e.target.value })
                  }
                />
                {fixedTimes[i] && (
                  <button
                    type="button"
                    onClick={() => {
                      const newFixedTimes = { ...fixedTimes };
                      delete newFixedTimes[i];
                      setFixedTimes(newFixedTimes);
                    }}
                    style={{ cursor: "pointer", padding: "4px 8px" }}
                  >
                    Clear
                  </button>
                )}
              </label>
            </div>
          </div>
        ))}
      </div>

      <button
        type="submit"
        disabled={loading}
        style={{
          marginTop: 24,
          padding: "12px 24px",
          fontSize: 16,
          cursor: loading ? "wait" : "pointer",
          backgroundColor: "#2196F3",
          color: "white",
          border: "none",
          borderRadius: 4,
        }}
      >
        {loading ? "Saving..." : "Save Constraints & Continue"}
      </button>
    </form>
  );
}
