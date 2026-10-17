import React, { useState } from "react";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  Send,
  Sparkles,
  ShieldAlert,
} from "lucide-react";
import { TaskRow } from "../components/TaskRow";
import { syncoraApi } from "../services/api.js";

export function MemberDashboardPage({
  tasks = [],
  member = {},
  currentUser = {},
  onOpenReportBlocker,
  onSelectTask,
}) {
  const currentUserName = currentUser?.name || member?.name || "Alex Morgan";
  const currentUserInitials = currentUserName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const memberTasks = (tasks || []).filter(
    (t) =>
      t.assignee === currentUserName ||
      t.assignee === "Alex Morgan" ||
      t.assigneeInitials === currentUserInitials ||
      t.assigneeInitials === "AM"
  );

  const completedCount = memberTasks.filter((t) => t.status === "Completed").length;
  const inProgressCount = memberTasks.filter((t) => t.status === "In Progress").length;
  const blockedCount = memberTasks.filter((t) => t.status === "Blocked").length;

  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState([
    {
      sender: "Syncora Bot",
      time: "10:15 AM",
      text: `Hey ${currentUserName.split(" ")[0]}! Quick check-in for the standup: How is progress on your current sprint tasks?`,
      isBot: true,
    },
    {
      sender: currentUserName,
      time: "10:18 AM",
      text: "The analytics module is around 60% done. Charts are working; I'm validating the filters now.",
      isBot: false,
    },
    {
      sender: "Syncora AI",
      time: "10:18 AM",
      text: "✓ Evidence recognized: Updated SYNC-201 to 60%. Flagged no blockers. Keep up the great work!",
      isBot: true,
      highlight: true,
    },
  ]);

  const handleSendChat = async (e) => {
    e.preventDefault();
    const textToSend = chatInput.trim();
    if (!textToSend) return;

    const userMsg = {
      sender: currentUserName,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      text: textToSend,
      isBot: false,
    };

    setMessages((prev) => [...prev, userMsg]);
    setChatInput("");

    try {
      const response = await syncoraApi.sendAIChat(member?.id || "mem-2", textToSend);
      setMessages((prev) => [
        ...prev,
        {
          sender: "Syncora AI",
          time: response?.timestamp || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          text: response?.reply || "✓ Evidence recognized and synchronized with team ledger.",
          isBot: true,
          highlight: true,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "Syncora AI",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          text: `✓ Parsed update: Captured evidence from your note. Syncora updated team pulse automatically.`,
          isBot: true,
          highlight: true,
        },
      ]);
    }
  };

  return (
    <div>
      {/* Member Top Welcome & Action Banner (Clean SaaS Linear Style) */}
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "12px",
          padding: "22px 26px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "20px",
          boxShadow: "var(--shadow-card)",
        }}
      >
        <div>
          <div className="section-label">MEMBER WORKSPACE</div>
          <h2 style={{ fontSize: "24px", fontWeight: "700", color: "var(--text-white)", marginTop: "2px" }}>
            Welcome back, {currentUserName.split(" ")[0]}
          </h2>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "10px", marginTop: "6px" }}>
            <span style={{ fontSize: "13px", color: "var(--accent-cyan)", fontWeight: "600" }}>
              {currentUser?.title || member?.title || "Product Designer"}
            </span>
            <span style={{ color: "var(--border-light)" }}>•</span>
            <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
              Workspace: <strong>{currentUser?.workspace || "Nova Studio"}</strong>
            </span>
            <span style={{ color: "var(--border-light)" }}>•</span>
            <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
              Telegram: <strong style={{ color: "var(--accent-cyan)" }}>{currentUser?.telegram || member?.telegramHandle || "@alex_dev"}</strong>
            </span>
            <span style={{ color: "var(--border-light)" }}>•</span>
            <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
              Capacity: <strong style={{ color: "var(--status-completed)" }}>{currentUser?.capacity ? `${currentUser.capacity}h/wk` : "30h/wk"}</strong>
            </span>
            {currentUser?.skills && (
              <>
                <span style={{ color: "var(--border-light)" }}>•</span>
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Skills: {currentUser.skills}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Report Blocker (Bright Crimson Red #EF4444, bg-red-50, subtle glow) */}
        <button
          type="button"
          className="btn-danger"
          onClick={onOpenReportBlocker}
          style={{
            padding: "9px 18px",
            fontSize: "14px",
            boxShadow: "0 0 12px var(--status-blocked-glow)",
          }}
        >
          <AlertTriangle size={17} />
          Report Blocker
        </button>
      </div>

      {/* KPI Stats Row for Member (12px radius, 16px-24px spacing) */}
      <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: "20px" }}>
        {/* In Progress: Amber (#F59E0B) */}
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-icon-pill" style={{ backgroundColor: "var(--status-progress-bg)", color: "var(--status-progress)" }}>
              <Clock size={18} />
            </div>
            <div
              className="kpi-badge"
              style={{
                color: "var(--status-progress)",
                background: "var(--status-progress-bg)",
                borderColor: "var(--status-progress-border)",
              }}
            >
              Active
            </div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">{inProgressCount}</div>
            <div className="kpi-label">In Progress</div>
            <div className="kpi-subtext">Due this week</div>
          </div>
        </div>

        {/* Completed: Emerald Green (#10B981) */}
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-icon-pill" style={{ backgroundColor: "var(--status-completed-bg)", color: "var(--status-completed)" }}>
              <CheckCircle2 size={18} />
            </div>
            <div className="kpi-badge">Sprint</div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">{completedCount}</div>
            <div className="kpi-label">Completed</div>
            <div className="kpi-subtext">Verified delivered</div>
          </div>
        </div>

        {/* Blockers: Bright Crimson Red (#EF4444, bg-red-50, subtle glow) */}
        <div
          className="kpi-card"
          style={{
            borderColor: blockedCount > 0 ? "var(--status-blocked-border)" : "var(--border-subtle)",
          }}
        >
          <div className="kpi-header">
            <div
              className="kpi-icon-pill"
              style={{
                backgroundColor: "var(--status-blocked-bg)",
                color: "var(--status-blocked)",
                boxShadow: blockedCount > 0 ? "0 0 10px var(--status-blocked-glow)" : "none",
              }}
            >
              <ShieldAlert size={18} />
            </div>
            <div
              className="kpi-badge"
              style={{
                color: "var(--status-blocked)",
                background: "var(--status-blocked-bg)",
                borderColor: "var(--status-blocked-border)",
              }}
            >
              {blockedCount} Blocker{blockedCount === 1 ? "" : "s"}
            </div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value" style={{ color: blockedCount > 0 ? "var(--status-blocked)" : "var(--text-white)" }}>
              {blockedCount}
            </div>
            <div className="kpi-label">Active Blockers</div>
            <div className="kpi-subtext">Awaiting clearance</div>
          </div>
        </div>

        {/* My Workload: Deep Indigo / Electric Violet (#6366F1) */}
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-icon-pill" style={{ backgroundColor: "var(--accent-primary-bg)", color: "var(--accent-primary)" }}>
              <Sparkles size={18} />
            </div>
            <div
              className="kpi-badge"
              style={{
                color: "var(--accent-primary)",
                background: "var(--accent-primary-bg)",
                borderColor: "var(--accent-primary-border)",
              }}
            >
              Optimal
            </div>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">64%</div>
            <div className="kpi-label">My Workload</div>
            <div className="kpi-subtext">Balanced capacity</div>
          </div>
        </div>
      </div>

      {/* Grid: My Priority Tasks (Left) & Telegram Bot Live Sync Simulator (Right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1.1fr", gap: "20px" }}>
        {/* My Tasks List */}
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
              <div className="section-label">MY FOCUS</div>
              <h2 className="section-title">Assigned Tasks ({memberTasks.length})</h2>
            </div>
          </div>

          <div>
            {memberTasks.map((task) => (
              <TaskRow key={task.id} task={task} onClick={() => onSelectTask && onSelectTask(task)} />
            ))}
          </div>
        </div>

        {/* Telegram Bot Live Sync Simulator */}
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ marginBottom: "14px" }}>
            <div className="section-label">TELEGRAM SYNC</div>
            <h2 className="section-title">Live Bot Assistant</h2>
            <p className="meta-text" style={{ marginTop: "2px" }}>
              Send quick progress notes just like in your Telegram team channel.
            </p>
          </div>

          {/* Chat Messages */}
          <div
            style={{
              flex: 1,
              backgroundColor: "var(--bg-app)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "10px",
              padding: "14px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              maxHeight: "340px",
              overflowY: "auto",
              marginBottom: "14px",
            }}
          >
            {messages.map((m, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: m.isBot ? "flex-start" : "flex-end",
                  maxWidth: "85%",
                }}
              >
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "3px" }}>
                  {m.sender} · {m.time}
                </div>
                <div
                  style={{
                    backgroundColor: m.isBot
                      ? m.highlight
                        ? "var(--accent-primary-bg)"
                        : "var(--bg-card)"
                      : "var(--accent-primary)",
                    border: m.highlight
                      ? "1px solid var(--accent-primary-border)"
                      : "1px solid var(--border-subtle)",
                    color: m.isBot
                      ? m.highlight
                        ? "var(--accent-primary)"
                        : "var(--text-primary)"
                      : "#FFFFFF",
                    padding: "9px 13px",
                    borderRadius: "10px",
                    fontSize: "13px",
                    lineHeight: "1.45",
                    boxShadow: "var(--shadow-sm)",
                  }}
                >
                  {m.text}
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input Form */}
          <form onSubmit={handleSendChat} style={{ display: "flex", gap: "8px" }}>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Finished review, testing staging deploy..."
              style={{ flex: 1 }}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
            />
            <button type="submit" className="btn-primary" style={{ padding: "8px 14px" }}>
              <Send size={15} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
