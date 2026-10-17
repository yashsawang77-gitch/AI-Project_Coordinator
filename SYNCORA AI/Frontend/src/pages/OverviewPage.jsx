import React, { useState } from "react";
import {
  CheckCircle2,
  TrendingUp,
  Calendar,
  AlertTriangle,
  ChevronRight,
  Sparkles,
  AlertCircle,
  Clock,
  Layers,
  Send,
  Check,
} from "lucide-react";
import { DonutChart } from "../components/DonutChart";
import { TaskRow } from "../components/TaskRow";

export function OverviewPage({
  stats = {},
  tasks = [],
  teamMembers = [],
  aiFeed = [],
  onNavigateToTasks,
  onSelectTask,
}) {
  const [actionStatus, setActionStatus] = useState(null);
  // Take top priority tasks for the priority list
  const priorityTasks = (tasks || []).slice(0, 4);

  return (
    <div>
      {/* 5 KPI Metric Cards Row (12px radius, 16px-24px balanced spacing) */}
      <div className="kpi-grid">
        {/* Total Tasks (Indigo / Violet) */}
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-icon-pill" style={{ backgroundColor: "var(--accent-primary-bg)", color: "var(--accent-primary)" }}>
              <Layers size={18} />
            </div>
            <div className="kpi-badge">↗ 12%</div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">{stats.totalTasks}</div>
            <div className="kpi-label">Total Tasks</div>
            <div className="kpi-subtext">{stats.totalTasksSub || "Across 3 projects"}</div>
          </div>
        </div>

        {/* Completed (Emerald Green #10B981) */}
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-icon-pill" style={{ backgroundColor: "var(--status-completed-bg)", color: "var(--status-completed)" }}>
              <CheckCircle2 size={18} />
            </div>
            <div className="kpi-badge">↗ 12%</div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">{stats.completed}</div>
            <div className="kpi-label">Completed</div>
            <div className="kpi-subtext">{stats.completedSub || "44% completion rate"}</div>
          </div>
        </div>

        {/* In Progress (Amber #F59E0B) */}
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-icon-pill" style={{ backgroundColor: "var(--status-progress-bg)", color: "var(--status-progress)" }}>
              <TrendingUp size={18} />
            </div>
            <div
              className="kpi-badge"
              style={{
                color: "var(--status-progress)",
                background: "var(--status-progress-bg)",
                borderColor: "var(--status-progress-border)",
              }}
            >
              ↗ 12%
            </div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">{stats.inProgress}</div>
            <div className="kpi-label">In Progress</div>
            <div className="kpi-subtext">{stats.inProgressSub || "5 due this week"}</div>
          </div>
        </div>

        {/* Pending (Slate Gray #64748B) */}
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-icon-pill" style={{ backgroundColor: "var(--status-pending-bg)", color: "var(--status-pending)" }}>
              <Clock size={18} />
            </div>
            <div
              className="kpi-badge"
              style={{
                color: "var(--status-pending)",
                background: "var(--status-pending-bg)",
                borderColor: "var(--status-pending-border)",
              }}
            >
              2 unassigned
            </div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">{stats.pending}</div>
            <div className="kpi-label">Pending</div>
            <div className="kpi-subtext">{stats.pendingSub || "Backlog queued"}</div>
          </div>
        </div>

        {/* Blocked (Bright Crimson Red #EF4444, bg-red-50, subtle glow) */}
        <div className="kpi-card" style={{ borderColor: "var(--status-blocked-border)" }}>
          <div className="kpi-header">
            <div
              className="kpi-icon-pill"
              style={{
                backgroundColor: "var(--status-blocked-bg)",
                color: "var(--status-blocked)",
                boxShadow: "0 0 10px var(--status-blocked-glow)",
              }}
            >
              <AlertTriangle size={18} />
            </div>
            <div
              className="kpi-badge"
              style={{
                color: "var(--status-blocked)",
                background: "var(--status-blocked-bg)",
                borderColor: "var(--status-blocked-border)",
              }}
            >
              Needs Action
            </div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value" style={{ color: "var(--status-blocked)" }}>
              {stats.blocked}
            </div>
            <div className="kpi-label">Blocked</div>
            <div className="kpi-subtext">{stats.blockedSub || "3 need attention"}</div>
          </div>
        </div>
      </div>

      {/* 🤖 Live Agent Interpretation Panel */}
      <div
        className="card"
        style={{
          marginBottom: "24px",
          border: "1px solid var(--border-subtle)",
          borderRadius: "12px",
          backgroundColor: "var(--bg-card)",
          boxShadow: "var(--shadow-card)",
          padding: "20px 24px",
        }}
      >
        {/* Card Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "18px",
            borderBottom: "1px solid var(--border-subtle)",
            paddingBottom: "14px",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "22px" }}>🤖</span>
            <div>
              <h2
                style={{
                  fontSize: "17px",
                  fontWeight: "700",
                  color: "var(--text-white)",
                  margin: 0,
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                Live Agent Interpretation
              </h2>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                Real-time conversational coordination stream via Telegram integration
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "11px",
                fontWeight: "700",
                color: "var(--status-completed)",
                backgroundColor: "var(--status-completed-bg)",
                border: "1px solid var(--status-completed-border)",
                padding: "3px 10px",
                borderRadius: "9999px",
                letterSpacing: "0.05em",
              }}
            >
              <span className="status-dot-pulse" />
              LIVE TELEGRAM PIPELINE
            </span>
            <span
              style={{
                fontSize: "12px",
                fontWeight: "600",
                color: "var(--accent-primary)",
                backgroundColor: "var(--accent-primary-bg)",
                border: "1px solid var(--accent-primary-border)",
                padding: "3px 10px",
                borderRadius: "9999px",
              }}
            >
              Confidence: 94%
            </span>
          </div>
        </div>

        {/* Two-Column Grid: Left = Incoming Telegram Message, Right = AI Extraction & Actions */}
        <div style={{ display: "grid", gridTemplateColumns: "1.05fr 1.35fr", gap: "20px", alignItems: "start" }}>
          {/* Left: Incoming Message (Simulated Chat Bubble from Telegram) */}
          <div
            style={{
              backgroundColor: "var(--bg-app)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "50%",
                    backgroundColor: "var(--accent-cyan)",
                    color: "#ffffff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "12px",
                    fontWeight: "700",
                  }}
                >
                  K
                </div>
                <div>
                  <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-white)" }}>
                    Kabir
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    @kabir_dev · Telegram #payments-core
                  </div>
                </div>
              </div>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "600",
                  color: "var(--accent-cyan)",
                  backgroundColor: "var(--accent-cyan-bg)",
                  padding: "2px 8px",
                  borderRadius: "6px",
                }}
              >
                Telegram Inbound
              </span>
            </div>

            {/* Simulated Chat Bubble */}
            <div
              style={{
                backgroundColor: "var(--bg-card)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "0 10px 10px 10px",
                padding: "12px 14px",
                fontSize: "14px",
                lineHeight: "1.5",
                color: "var(--text-primary)",
                position: "relative",
              }}
            >
              “The API is connected, but I am waiting for test credentials.”
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", textAlign: "right" }}>
                10:42 AM · SSL Verified
              </div>
            </div>

            {/* AI Reasoning Note */}
            <div
              style={{
                backgroundColor: "var(--accent-primary-bg)",
                border: "1px solid var(--accent-primary-border)",
                borderRadius: "8px",
                padding: "10px 12px",
                fontSize: "12px",
                color: "var(--text-secondary)",
                lineHeight: "1.45",
              }}
            >
              <strong style={{ color: "var(--accent-primary)" }}>🧠 AI Reasoning Note:</strong>{" "}
              Member reported code connection progress, but explicitly declared an unresolved external dependency/credential blocker.
            </div>
          </div>

          {/* Right: AI Extraction Details & Action Buttons */}
          <div
            style={{
              backgroundColor: "var(--bg-app)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
            }}
          >
            {/* Extraction Fields Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              {/* Detected Task */}
              <div>
                <div className="section-label" style={{ fontSize: "11px", marginBottom: "3px" }}>
                  DETECTED TASK
                </div>
                <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-white)" }}>
                  Connect Payment API
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>ID: SYNC-204 · Payments</div>
              </div>

              {/* Inferred Status */}
              <div>
                <div className="section-label" style={{ fontSize: "11px", marginBottom: "3px" }}>
                  INFERRED STATUS
                </div>
                <div>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "12px",
                      fontWeight: "700",
                      backgroundColor: "var(--status-blocked-bg)",
                      color: "var(--status-blocked)",
                      border: "1px solid var(--status-blocked-border)",
                      padding: "4px 10px",
                      borderRadius: "6px",
                      boxShadow: "0 0 10px var(--status-blocked-glow)",
                      letterSpacing: "0.04em",
                    }}
                  >
                    <AlertTriangle size={13} />
                    BLOCKED
                  </span>
                  <span style={{ fontSize: "11px", color: "var(--status-blocked)", display: "block", marginTop: "2px", fontWeight: "500" }}>
                    (Not marked Completed)
                  </span>
                </div>
              </div>
            </div>

            {/* Progress: 70% Progress Bar */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                <span className="section-label" style={{ fontSize: "11px" }}>PROGRESS</span>
                <span style={{ fontSize: "13px", fontWeight: "700", color: "var(--accent-primary)" }}>70%</span>
              </div>
              <div className="pulse-progress-track" style={{ height: "7px" }}>
                <div
                  className="pulse-progress-fill"
                  style={{
                    width: "70%",
                    backgroundColor: "var(--accent-primary)",
                  }}
                />
              </div>
            </div>

            {/* Identified Blocker & AI Confidence */}
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: "12px" }}>
              <div
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  backgroundColor: "var(--status-blocked-bg)",
                  border: "1px solid var(--status-blocked-border)",
                }}
              >
                <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--status-blocked)" }}>
                  IDENTIFIED BLOCKER
                </div>
                <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--status-blocked)", marginTop: "2px" }}>
                  Missing test credentials
                </div>
              </div>

              <div
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  backgroundColor: "var(--bg-card)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)" }}>
                  AI CONFIDENCE
                </div>
                <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--status-completed)", marginTop: "2px" }}>
                  94% High
                </div>
              </div>
            </div>

            {/* Interactive Feedback Notice (if action taken) */}
            {actionStatus && (
              <div
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  fontSize: "12px",
                  fontWeight: "600",
                  backgroundColor:
                    actionStatus === "approved"
                      ? "var(--status-completed-bg)"
                      : actionStatus === "clarification"
                      ? "var(--accent-cyan-bg)"
                      : "var(--status-progress-bg)",
                  color:
                    actionStatus === "approved"
                      ? "var(--status-completed)"
                      : actionStatus === "clarification"
                      ? "var(--accent-cyan)"
                      : "var(--status-progress)",
                  border: `1px solid ${
                    actionStatus === "approved"
                      ? "var(--status-completed-border)"
                      : actionStatus === "clarification"
                      ? "var(--accent-cyan)"
                      : "var(--status-progress-border)"
                  }`,
                }}
              >
                {actionStatus === "approved" && "✓ Status Approved: BLOCKED flagged in team queue and standup sync."}
                {actionStatus === "clarification" && "✓ Telegram Ping Sent: Prompted @kabir_dev for credential details."}
                {actionStatus === "override" && "✓ Leader Override Applied: Reclassified to In Progress (Active)."}
              </div>
            )}

            {/* Action Buttons: Quick buttons for [Approve Status], [Request Clarification in Telegram], and [Override] */}
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "2px" }}>
              <button
                type="button"
                className="btn-primary"
                onClick={() => setActionStatus("approved")}
                style={{
                  padding: "8px 14px",
                  fontSize: "13px",
                  backgroundColor: actionStatus === "approved" ? "var(--status-completed)" : "var(--accent-primary)",
                  color: "#ffffff",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  cursor: "pointer",
                }}
              >
                <Check size={14} />
                Approve Status
              </button>

              <button
                type="button"
                className="btn-secondary"
                onClick={() => setActionStatus("clarification")}
                style={{
                  padding: "8px 14px",
                  fontSize: "13px",
                  color: "var(--accent-cyan)",
                  borderColor: "var(--accent-cyan)",
                  backgroundColor: actionStatus === "clarification" ? "var(--accent-cyan-bg)" : "transparent",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  cursor: "pointer",
                }}
              >
                <Send size={14} />
                Request Clarification in Telegram
              </button>

              <button
                type="button"
                className="btn-secondary"
                onClick={() => setActionStatus("override")}
                style={{
                  padding: "8px 14px",
                  fontSize: "13px",
                  color: "var(--text-secondary)",
                  backgroundColor: actionStatus === "override" ? "var(--bg-card)" : "transparent",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  cursor: "pointer",
                }}
              >
                Override
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mid Section: Priority Tasks (Left) & Real-Time Task Distribution (Right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1.65fr 1fr", gap: "20px", marginBottom: "20px" }}>
        {/* Priority Tasks Card */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div
            style={{
              padding: "18px 22px",
              borderBottom: "1px solid var(--border-subtle)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div className="section-label">LIVE WORKFLOW</div>
              <h2 className="section-title">Priority tasks</h2>
            </div>
            <button
              type="button"
              onClick={onNavigateToTasks}
              style={{
                background: "none",
                border: "none",
                color: "var(--accent-primary)",
                fontSize: "13px",
                fontWeight: "600",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              View all <ChevronRight size={15} />
            </button>
          </div>

          <div>
            {priorityTasks.map((task) => (
              <TaskRow key={task.id} task={task} onClick={() => onSelectTask && onSelectTask(task)} />
            ))}
          </div>
        </div>

        {/* Real-time Task Distribution Donut Card */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "12px" }}>
            <div>
              <div className="section-label">REAL-TIME</div>
              <h2 className="section-title">Task distribution</h2>
            </div>
          </div>

          <DonutChart
            completed={stats.completed}
            inProgress={stats.inProgress}
            pending={stats.pending}
            blocked={stats.blocked}
            total={stats.totalTasks}
          />
        </div>
      </div>

      {/* Bottom Section: AI Activity Feed (Left) & Team Pulse Capacity (Right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1.65fr 1fr", gap: "20px" }}>
        {/* AI Activity Feed */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
            <div>
              <div className="section-label">AI ACTIVITY</div>
              <h2 className="section-title">Syncora intelligence feed</h2>
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "11px",
                fontWeight: "700",
                color: "var(--status-completed)",
                letterSpacing: "0.08em",
              }}
            >
              <span className="status-dot-pulse" />
              LIVE
            </div>
          </div>

          <div className="activity-feed-list">
            {(aiFeed || []).map((item) => (
              <div key={item.id} className="activity-feed-item">
                <div className="activity-item-left">
                  <div
                    className="activity-item-icon"
                    style={{
                      backgroundColor:
                        item.type === "blocker_detected"
                          ? "var(--status-blocked-bg)"
                          : item.type === "status_update"
                          ? "var(--status-completed-bg)"
                          : "var(--accent-primary-bg)",
                      color:
                        item.type === "blocker_detected"
                          ? "var(--status-blocked)"
                          : item.type === "status_update"
                          ? "var(--status-completed)"
                          : "var(--accent-primary)",
                    }}
                  >
                    {item.type === "blocker_detected" ? (
                      <AlertCircle size={16} />
                    ) : item.type === "status_update" ? (
                      <CheckCircle2 size={16} />
                    ) : (
                      <Sparkles size={16} />
                    )}
                  </div>
                  <div>
                    <div className="activity-item-title">{item.title}</div>
                    <div className="activity-item-desc">{item.description}</div>
                    <div className="activity-item-time">{item.timeAgo}</div>
                  </div>
                </div>

                {/* Feed Badge */}
                <div>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: "600",
                      padding: "2px 8px",
                      borderRadius: "10px",
                      backgroundColor:
                        item.badgeType === "attention"
                          ? "var(--status-blocked-bg)"
                          : item.badgeType === "verified"
                          ? "var(--status-completed-bg)"
                          : "var(--accent-primary-bg)",
                      color:
                        item.badgeType === "attention"
                          ? "var(--status-blocked)"
                          : item.badgeType === "verified"
                          ? "var(--status-completed)"
                          : "var(--accent-primary)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    {item.badgeText}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Capacity / Team Pulse */}
        <div className="card">
          <div style={{ marginBottom: "8px" }}>
            <div className="section-label">CAPACITY</div>
            <h2 className="section-title">Team pulse</h2>
          </div>

          <div className="pulse-list">
            {(teamMembers || []).slice(0, 3).map((member) => {
              const isOverloaded = member.workload >= 90;
              const progressFillColor = isOverloaded ? "var(--status-blocked)" : "var(--accent-primary)";

              return (
                <div key={member.id} className="pulse-member-row">
                  <div className="pulse-member-header">
                    <div className="pulse-member-info">
                      <div
                        className="pulse-member-avatar"
                        style={{ backgroundColor: member.avatarBg || "var(--accent-primary)" }}
                      >
                        {member.initials}
                      </div>
                      <div>
                        <div className="pulse-member-name">{member.name}</div>
                        <div className="pulse-member-tasks">{member.activeTasks} active tasks</div>
                      </div>
                    </div>
                    <div
                      className="pulse-percent"
                      style={{ color: isOverloaded ? "var(--status-blocked)" : "var(--text-white)" }}
                    >
                      {member.workload}%
                    </div>
                  </div>

                  <div className="pulse-progress-track">
                    <div
                      className="pulse-progress-fill"
                      style={{
                        width: `${member.workload}%`,
                        backgroundColor: progressFillColor,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
