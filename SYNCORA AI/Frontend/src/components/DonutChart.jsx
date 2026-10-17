import React from "react";

export function DonutChart({
  completed = 21,
  inProgress = 12,
  pending = 8,
  blocked = 7,
  total = 48,
}) {
  const size = 180;
  const strokeWidth = 16;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  // Segments calculation
  const totalCount = total || completed + inProgress + pending + blocked || 1;

  // Exact Status Colors Requested by User:
  // Completed: Emerald Green (#10B981)
  // In Progress: Amber (#F59E0B)
  // Blocked: Bright Crimson Red (#EF4444)
  // Pending: Slate Gray (#64748B)
  const segments = [
    { label: "Completed", count: completed, color: "#10B981", dotColor: "#10B981" },
    { label: "In progress", count: inProgress, color: "#F59E0B", dotColor: "#F59E0B" },
    { label: "Blocked", count: blocked, color: "#EF4444", dotColor: "#EF4444" },
    { label: "Pending", count: pending, color: "#64748B", dotColor: "#64748B" },
  ];

  // Calculate stroke dash arrays
  let accumulatedPercent = 0;
  const strokeSegments = segments.map((seg) => {
    const percent = seg.count / totalCount;
    const strokeDasharray = `${percent * circumference} ${circumference}`;
    const strokeDashoffset = -accumulatedPercent * circumference;
    accumulatedPercent += percent;

    return {
      ...seg,
      strokeDasharray,
      strokeDashoffset,
      percent: Math.round(percent * 100),
    };
  });

  return (
    <div className="donut-chart-container">
      <div style={{ position: "relative", width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{ transform: "rotate(-90deg)" }}
        >
          {/* Base Track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="transparent"
            stroke="var(--border-subtle)"
            strokeWidth={strokeWidth}
          />

          {/* Slices */}
          {strokeSegments.map((seg, idx) => (
            <circle
              key={idx}
              cx={center}
              cy={center}
              r={radius}
              fill="transparent"
              stroke={seg.color}
              strokeWidth={strokeWidth}
              strokeDasharray={seg.strokeDasharray}
              strokeDashoffset={seg.strokeDashoffset}
              strokeLinecap="round"
              style={{
                transition: "stroke-dashoffset 0.8s ease, stroke-dasharray 0.8s ease",
              }}
            />
          ))}
        </svg>

        {/* Center Text */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            pointerEvents: "none",
          }}
        >
          <span style={{ fontSize: "32px", fontWeight: "800", color: "var(--text-white)", lineHeight: 1 }}>
            {totalCount}
          </span>
          <span
            style={{
              fontSize: "11px",
              fontWeight: "600",
              color: "var(--text-muted)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              marginTop: "4px",
            }}
          >
            Tasks Total
          </span>
        </div>
      </div>

      {/* Legend Grid */}
      <div className="donut-legend">
        {strokeSegments.map((seg, idx) => (
          <div key={idx} className="legend-item">
            <div className="legend-item-left">
              <span className="legend-dot" style={{ backgroundColor: seg.dotColor }} />
              <span>{seg.label}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span className="legend-count">{seg.count}</span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>({seg.percent}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
