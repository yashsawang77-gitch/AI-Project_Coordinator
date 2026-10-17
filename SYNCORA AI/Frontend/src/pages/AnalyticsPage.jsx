import React from "react";
import { DonutChart } from "../components/DonutChart";

export function AnalyticsPage({ stats, tasks }) {
  const projects = [
    { name: "Product Core", tasks: 24, completed: 14, inProgress: 8, blocked: 2, progress: 68 },
    { name: "Marketing Launch", tasks: 12, completed: 4, inProgress: 6, blocked: 2, progress: 42 },
    { name: "Infrastructure", tasks: 8, completed: 2, inProgress: 2, blocked: 4, progress: 30 },
    { name: "Growth", tasks: 4, completed: 1, inProgress: 2, blocked: 1, progress: 50 },
  ];

  return (
    <div>
      {/* Top Analytics Summary */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "24px", marginBottom: "24px" }}>
        {/* Real-time Donut Chart Card */}
        <div className="card">
          <div className="section-label">SPRINT DISTRIBUTION</div>
          <h2 className="section-title" style={{ marginBottom: "16px" }}>Task Status Equilibrium</h2>
          <DonutChart
            completed={stats.completed}
            inProgress={stats.inProgress}
            pending={stats.pending}
            blocked={stats.blocked}
            total={stats.totalTasks}
          />
        </div>

        {/* Velocity Metrics */}
        <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div className="section-label">TEAM VELOCITY</div>
            <h2 className="section-title">Sprint Health Metrics</h2>
            <p className="page-subtitle" style={{ fontSize: "14px", marginBottom: "20px" }}>
              AI telemetry captured through Telegram standup check-ins and Git commits.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ padding: "16px", backgroundColor: "var(--bg-app)", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
              <div className="meta-text">Average Resolution Time</div>
              <div style={{ fontSize: "24px", fontWeight: "700", color: "var(--status-completed)", marginTop: "4px" }}>
                18.4 hrs
              </div>
              <div style={{ fontSize: "12px", color: "var(--status-completed)", marginTop: "2px" }}>14% faster than baseline</div>
            </div>

            <div style={{ padding: "16px", backgroundColor: "var(--bg-app)", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
              <div className="meta-text">AI Verification Accuracy</div>
              <div style={{ fontSize: "24px", fontWeight: "700", color: "var(--accent-cyan)", marginTop: "4px" }}>
                94.8%
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>NLP reply confidence</div>
            </div>

            <div style={{ padding: "16px", backgroundColor: "var(--bg-app)", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
              <div className="meta-text">Blocker Clearance Rate</div>
              <div style={{ fontSize: "24px", fontWeight: "700", color: "var(--status-progress)", marginTop: "4px" }}>
                4.2 hrs
              </div>
              <div style={{ fontSize: "12px", color: "var(--status-progress)", marginTop: "2px" }}>Leader response speed</div>
            </div>

            <div style={{ padding: "16px", backgroundColor: "var(--bg-app)", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
              <div className="meta-text">Async Sync Ratio</div>
              <div style={{ fontSize: "24px", fontWeight: "700", color: "var(--accent-primary)", marginTop: "4px" }}>
                87%
              </div>
              <div style={{ fontSize: "12px", color: "var(--accent-primary)", marginTop: "2px" }}>Zero meetings needed</div>
            </div>
          </div>
        </div>
      </div>

      {/* Project Progress Breakdown */}
      <div className="card">
        <div className="section-label">PROJECT PORTFOLIO</div>
        <h2 className="section-title" style={{ marginBottom: "16px" }}>Workload Distribution by Project</h2>

        <div className="tasks-container-card" style={{ border: "none" }}>
          <div className="table-header-row" style={{ gridTemplateColumns: "2fr 1fr 1fr 1.5fr" }}>
            <div>PROJECT</div>
            <div>TASKS</div>
            <div>COMPLETED</div>
            <div>SPRINT COMPLETION PROGRESS</div>
          </div>

          {projects.map((proj, idx) => (
            <div key={idx} className="task-row" style={{ gridTemplateColumns: "2fr 1fr 1fr 1.5fr" }}>
              <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text-white)" }}>
                {proj.name}
              </div>
              <div style={{ fontSize: "14px", color: "var(--text-secondary)" }}>
                {proj.tasks} tasks
              </div>
              <div style={{ fontSize: "14px", color: "var(--status-completed)", fontWeight: "600" }}>
                {proj.completed} done
              </div>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "4px" }}>
                  <span style={{ color: "var(--text-muted)" }}>Progress</span>
                  <span style={{ color: "var(--status-completed)", fontWeight: "700" }}>{proj.progress}%</span>
                </div>
                <div className="pulse-progress-track">
                  <div
                    className="pulse-progress-fill"
                    style={{
                      width: `${proj.progress}%`,
                      backgroundColor: "var(--status-completed)",
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
