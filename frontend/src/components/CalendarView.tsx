import type { ScheduledBlock } from "../api";

interface Props {
  schedule: ScheduledBlock[];
  windowStart: string;
  windowEnd: string;
  algorithm: string | null;
}

export function CalendarView({ schedule, windowStart, windowEnd, algorithm }: Props) {
  const parseTime = (time: string): number => {
    const [hours, minutes] = time.split(":").map(Number);
    return hours * 60 + minutes;
  };

  const formatTime = (time: string): string => {
    return time;
  };

  const startMinutes = parseTime(windowStart);
  const endMinutes = parseTime(windowEnd);
  const totalMinutes = endMinutes - startMinutes;

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

  const hourMarkers: string[] = [];
  const startHour = Math.floor(startMinutes / 60);
  const endHour = Math.ceil(endMinutes / 60);
  for (let h = startHour; h <= endHour; h++) {
    hourMarkers.push(`${h.toString().padStart(2, "0")}:00`);
  }

  return (
    <div style={{ marginTop: 20 }}>
      <h2>Your Schedule</h2>
      {algorithm && (
        <div
          style={{
            display: "inline-block",
            padding: "4px 12px",
            backgroundColor: "#e3f2fd",
            borderRadius: 4,
            marginBottom: 12,
            fontSize: 14,
          }}
        >
          Generated using: <strong>{algorithm}</strong> algorithm
        </div>
      )}
      <div
        style={{
          position: "relative",
          height: 500,
          border: "1px solid #ddd",
          borderRadius: 8,
          backgroundColor: "#fafafa",
          marginTop: 10,
        }}
      >
        {hourMarkers.map((time) => {
          const minutes = parseTime(time);
          const top = ((minutes - startMinutes) / totalMinutes) * 100;
          if (top < 0 || top > 100) return null;
          return (
            <div
              key={time}
              style={{
                position: "absolute",
                top: `${top}%`,
                left: 0,
                right: 0,
                borderTop: "1px dashed #ddd",
                paddingLeft: 5,
                fontSize: 12,
                color: "#888",
              }}
            >
              {time}
            </div>
          );
        })}

        {schedule.map((block, i) => {
          const blockStart = parseTime(block.start_time);
          const blockEnd = parseTime(block.end_time);
          const top = ((blockStart - startMinutes) / totalMinutes) * 100;
          const height = ((blockEnd - blockStart) / totalMinutes) * 100;

          return (
            <div
              key={i}
              style={{
                position: "absolute",
                top: `${top}%`,
                left: 50,
                right: 10,
                height: `${height}%`,
                backgroundColor: categoryColor(block.category),
                borderRadius: 4,
                padding: 8,
                color: "white",
                overflow: "hidden",
                boxSizing: "border-box",
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
              }}
            >
              <div style={{ fontWeight: "bold", fontSize: 14 }}>
                {block.description}
              </div>
              <div style={{ fontSize: 12, opacity: 0.9 }}>
                {formatTime(block.start_time)} - {formatTime(block.end_time)}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: 20 }}>
        <h3>Schedule List</h3>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ backgroundColor: "#f0f0f0" }}>
              <th style={{ padding: 10, textAlign: "left", borderBottom: "2px solid #ddd" }}>
                Time
              </th>
              <th style={{ padding: 10, textAlign: "left", borderBottom: "2px solid #ddd" }}>
                Task
              </th>
              <th style={{ padding: 10, textAlign: "left", borderBottom: "2px solid #ddd" }}>
                Category
              </th>
            </tr>
          </thead>
          <tbody>
            {schedule.map((block, i) => (
              <tr key={i}>
                <td style={{ padding: 10, borderBottom: "1px solid #eee" }}>
                  {formatTime(block.start_time)} - {formatTime(block.end_time)}
                </td>
                <td style={{ padding: 10, borderBottom: "1px solid #eee" }}>
                  {block.description}
                </td>
                <td style={{ padding: 10, borderBottom: "1px solid #eee" }}>
                  <span
                    style={{
                      padding: "2px 8px",
                      borderRadius: 4,
                      backgroundColor: categoryColor(block.category),
                      color: "white",
                      fontSize: 12,
                    }}
                  >
                    {block.category}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
