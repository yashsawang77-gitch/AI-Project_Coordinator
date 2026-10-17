import React from "react";
import {
  ShieldAlert,
  ArrowRight,
  CheckCircle2,
  Info,
} from "lucide-react";

export function WorkloadPage({
  recommendations = [],
  members = [],
  onReviewReassignment,
}) {
  return (
    <div>
      {/* Overview Alert Banner (Clean Light SaaS style with Crimson Red accent) */}
      <div
        style={{
          background: "var(--status-blocked-bg)",
          border: "1px solid var(--status-blocked-border)",
          borderRadius: "12px",
          padding: "24px 28px",
          marginBottom: "24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxShadow: "0 0 16px var(--status-blocked-glow)",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", gap: "16px" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "10px",
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--status-blocked)",
              flexShrink: 0,
            }}
          >
            <ShieldAlert size={24} />
          </div>
          <div>
            <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--status-blocked)", letterSpacing: "0.08em" }}>
              WORKLOAD IMBALANCE DETECTED
            </div>
            <h2 style={{ fontSize: "20px", fontWeight: "700", color: "var(--text-white)", marginTop: "2px" }}>
              1 Team Member Critically Overloaded & 1 Preemptive Risk
            </h2>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", marginTop: "4px", maxWidth: "700px" }}>
              Leo Park is operating at <strong style={{ color: "var(--status-blocked)" }}>92% capacity</strong> with 7 active tasks and a blocked dependency.
              Reallocating estimated effort to available members will restore operational health.
            </p>
          </div>
        </div>

        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "32px", fontWeight: "800", color: "var(--status-blocked)" }}>78%</div>
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>Equilibrium Index</div>
        </div>
      </div>

      {/* AI Workload Recommendations Section */}
      <div style={{ marginBottom: "28px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
          <div>
            <div className="section-label">AI RECOMMENDATIONS</div>
            <h2 className="section-title">Invisible Workload Rebalancing</h2>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "var(--text-muted)" }}>
            <Info size={15} />
            <span>Leader approval required for all reassignments</span>
          </div>
        </div>

        {(recommendations || []).length === 0 ? (
          <div
            className="card"
            style={{
              padding: "40px",
              textAlign: "center",
              color: "var(--status-completed)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <CheckCircle2 size={36} />
            <div style={{ fontSize: "18px", fontWeight: "700", color: "var(--text-white)" }}>
              Team Capacity in Perfect Equilibrium
            </div>
            <p className="meta-text">All active tasks and blockers are currently balanced across members.</p>
          </div>
        ) : (
          (recommendations || []).map((rec) => (
            <div
              key={rec.id}
              className={`workload-alert-card ${rec.priority === "Preemptive" ? "preemptive" : ""}`}
            >
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span
                    style={{
                      fontSize: "12px",
                      fontWeight: "700",
                      padding: "3px 10px",
                      borderRadius: "12px",
                      backgroundColor:
                        rec.priority === "High Urgency"
                          ? "var(--status-blocked-bg)"
                          : "var(--status-progress-bg)",
                      color: rec.priority === "High Urgency" ? "var(--status-blocked)" : "var(--status-progress)",
                      border: `1px solid ${
                        rec.priority === "High Urgency" ? "var(--status-blocked-border)" : "var(--status-progress-border)"
                      }`,
                      letterSpacing: "0.05em",
                    }}
                  >
                    {rec.priority}
                  </span>
                  <span style={{ fontSize: "14px", color: "var(--text-muted)" }}>
                    Confidence: <strong style={{ color: "var(--status-completed)" }}>{rec.taskToReassign.confidence}</strong>
                  </span>
                </div>

                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => onReviewReassignment(rec)}
                  style={{
                    padding: "7px 16px",
                    fontSize: "14px",
                    backgroundColor: rec.priority === "High Urgency" ? "var(--status-blocked)" : "var(--accent-primary)",
                    color: "#ffffff",
                    boxShadow: "none",
                  }}
                >
                  Review Reassignment
                </button>
              </div>

              {/* Task Details & Transfer Visualization */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1.5fr 1fr",
                  gap: "20px",
                  alignItems: "center",
                  backgroundColor: "var(--bg-app)",
                  border: "1px solid var(--border-subtle)",
                  padding: "16px 20px",
                  borderRadius: "10px",
                  marginBottom: "14px",
                }}
              >
                <div>
                  <div style={{ fontSize: "15px", fontWeight: "700", color: "var(--text-white)" }}>
                    {rec.taskToReassign.id} · {rec.taskToReassign.title}
                  </div>
                  <div style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "2px" }}>
                    Project: {rec.taskToReassign.project} | Estimated Effort:{" "}
                    <span style={{ color: "var(--text-white)" }}>{rec.taskToReassign.estimatedHours}</span>
                  </div>
                  {rec.taskToReassign.uncertainty && (
                    <div style={{ fontSize: "13px", color: "var(--status-progress)", marginTop: "4px" }}>
                      Note: {rec.taskToReassign.uncertainty}
                    </div>
                  )}
                </div>

                {/* Transfer Pill */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    gap: "12px",
                  }}
                >
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-white)" }}>
                      {rec.overburdenedMember}
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--status-blocked)", fontWeight: "600" }}>{rec.currentLoad}% Load</div>
                  </div>
                  <ArrowRight size={18} color="var(--text-muted)" />
                  <div style={{ textAlign: "left" }}>
                    <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-white)" }}>
                      {rec.suggestedMember}
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--status-completed)", fontWeight: "600" }}>{rec.suggestedLoad}% Load</div>
                  </div>
                </div>
              </div>

              {/* AI Reasoning */}
              <div style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                <strong style={{ color: "var(--text-white)" }}>AI Insight:</strong> {rec.reasoning}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Member Capacity Ledger */}
      <div className="card">
        <div style={{ marginBottom: "16px" }}>
          <div className="section-label">TEAM CAPACITY LEDGER</div>
          <h2 className="section-title">Verified Member Allocation</h2>
        </div>

        <div className="tasks-container-card" style={{ border: "none" }}>
          <div className="table-header-row" style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr" }}>
            <div>MEMBER</div>
            <div>STATUS</div>
            <div>ACTIVE TASKS</div>
            <div>COMPLETION</div>
            <div>CAPACITY LOAD</div>
          </div>

          {(members || []).map((member) => (
            <div
              key={member.id}
              className="task-row"
              style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div
                  className="pulse-member-avatar"
                  style={{ backgroundColor: member.avatarBg || "var(--accent-primary)", width: "32px", height: "32px" }}
                >
                  {member.initials}
                </div>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-white)" }}>{member.name}</div>
                  <div className="meta-text">{member.title}</div>
                </div>
              </div>

              <div>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: "600",
                    padding: "2px 8px",
                    borderRadius: "10px",
                    backgroundColor:
                      member.workload >= 90
                        ? "var(--status-blocked-bg)"
                        : member.workload <= 50
                        ? "var(--status-completed-bg)"
                        : "var(--accent-cyan-bg)",
                    color:
                      member.workload >= 90
                        ? "var(--status-blocked)"
                        : member.workload <= 50
                        ? "var(--status-completed)"
                        : "var(--accent-cyan)",
                    border: `1px solid ${
                      member.workload >= 90
                        ? "var(--status-blocked-border)"
                        : member.workload <= 50
                        ? "var(--status-completed-border)"
                        : "var(--accent-primary-border)"
                    }`,
                  }}
                >
                  {member.workloadStatus}
                </span>
              </div>

              <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-white)" }}>
                {member.activeTasks}
              </div>

              <div style={{ fontSize: "14px", color: "var(--text-muted)" }}>
                {member.completionRate}%
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "4px" }}>
                  <span style={{ color: member.workload >= 90 ? "var(--status-blocked)" : "var(--text-white)", fontWeight: "700" }}>
                    {member.workload}%
                  </span>
                </div>
                <div className="pulse-progress-track">
                  <div
                    className="pulse-progress-fill"
                    style={{
                      width: `${member.workload}%`,
                      backgroundColor: member.workload >= 90 ? "var(--status-blocked)" : "var(--status-completed)",
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
