import { useState } from "react";

interface Props {
  onSubmit: (tasks: string[]) => void;
  loading: boolean;
}

export function TaskInput({ onSubmit, loading }: Props) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const tasks = input
      .split("\n")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
    if (tasks.length > 0) {
      onSubmit(tasks);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Step 2: Enter Your Tasks</h2>
      <p>Type your tasks for today (one per line). They will be automatically categorized.</p>

      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Go to gym&#10;Review quarterly report&#10;Call mom&#10;Meditate for 15 minutes&#10;Prepare presentation&#10;Take vitamins"
        rows={10}
        style={{
          width: "100%",
          padding: 12,
          fontSize: 16,
          fontFamily: "inherit",
          boxSizing: "border-box",
          borderRadius: 4,
          border: "1px solid #ddd",
        }}
      />

      <button
        type="submit"
        disabled={loading || input.trim().length === 0}
        style={{
          marginTop: 16,
          padding: "12px 24px",
          fontSize: 16,
          cursor: loading ? "wait" : "pointer",
          backgroundColor: "#2196F3",
          color: "white",
          border: "none",
          borderRadius: 4,
        }}
      >
        {loading ? "Categorizing..." : "Categorize Tasks & Continue"}
      </button>
    </form>
  );
}
