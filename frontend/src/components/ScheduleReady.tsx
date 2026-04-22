interface Props {
  onGenerate: () => void;
  loading: boolean;
}

export function ScheduleReady({ onGenerate, loading }: Props) {
  return (
    <div style={{ textAlign: "center", padding: 40 }}>
      <h2>Step 4: Generate Schedule</h2>
      <p style={{ color: "#666", marginBottom: 24 }}>
        All constraints are set. Click below to generate your optimized schedule.
        <br />
        The system will automatically select the best algorithm based on your constraints.
      </p>

      <div
        style={{
          padding: 20,
          backgroundColor: "#e3f2fd",
          borderRadius: 8,
          marginBottom: 24,
        }}
      >
        <strong>Algorithm Selection:</strong>
        <ul style={{ textAlign: "left", marginTop: 12, marginBottom: 0 }}>
          <li>
            <strong>Greedy</strong> — Used when all tasks fit in the time window
          </li>
          <li>
            <strong>Knapsack</strong> — Used when tasks exceed the window (maximizes utility)
          </li>
          <li>
            <strong>Permutation</strong> — Used when multiple fixed times need optimal ordering
          </li>
        </ul>
      </div>

      <button
        onClick={onGenerate}
        disabled={loading}
        style={{
          padding: "16px 32px",
          fontSize: 18,
          cursor: loading ? "wait" : "pointer",
          backgroundColor: "#4CAF50",
          color: "white",
          border: "none",
          borderRadius: 4,
        }}
      >
        {loading ? "Generating..." : "Generate Optimized Schedule"}
      </button>
    </div>
  );
}
