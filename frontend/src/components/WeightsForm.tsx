import { useState } from "react";
import type { UtilityWeights } from "../api";

interface Props {
  onSubmit: (weights: UtilityWeights) => void;
  loading: boolean;
}

export function WeightsForm({ onSubmit, loading }: Props) {
  const [weights, setWeights] = useState<UtilityWeights>({
    personal: 1.0,
    health: 1.0,
    work: 1.0,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(weights);
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

  return (
    <form onSubmit={handleSubmit}>
      <h2>Step 1: Set Priority Weights</h2>
      <p>Adjust how important each category is for scheduling priority.</p>

      <div style={{ padding: 20, backgroundColor: "#f5f5f5", borderRadius: 8 }}>
        {(["personal", "health", "work"] as const).map((cat) => (
          <div
            key={cat}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 16,
            }}
          >
            <span
              style={{
                padding: "4px 12px",
                borderRadius: 4,
                backgroundColor: categoryColor(cat.charAt(0).toUpperCase() + cat.slice(1)),
                color: "white",
                fontSize: 14,
                fontWeight: "bold",
                minWidth: 80,
                textAlign: "center",
              }}
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </span>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={weights[cat]}
              onChange={(e) =>
                setWeights({ ...weights, [cat]: parseFloat(e.target.value) })
              }
              style={{ flex: 1 }}
            />
            <span style={{ minWidth: 40, textAlign: "right", fontWeight: "bold" }}>
              {weights[cat].toFixed(1)}
            </span>
          </div>
        ))}
      </div>

      <button
        type="submit"
        disabled={loading}
        style={{
          marginTop: 20,
          padding: "12px 24px",
          fontSize: 16,
          cursor: loading ? "wait" : "pointer",
          backgroundColor: "#2196F3",
          color: "white",
          border: "none",
          borderRadius: 4,
        }}
      >
        {loading ? "Saving..." : "Save Weights & Continue"}
      </button>
    </form>
  );
}
