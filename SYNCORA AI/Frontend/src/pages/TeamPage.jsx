import React, { useState } from "react";
import { Check, Copy, RefreshCw, Link as LinkIcon, ShieldCheck, UserPlus } from "lucide-react";

export function TeamPage({ members = [], inviteCode = "NOVA-7X4K", currentUser }) {
  const [currentCode, setCurrentCode] = useState(inviteCode);
  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [joinCodeInput, setJoinCodeInput] = useState("");
  const [joinStatus, setJoinStatus] = useState(null);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(currentCode);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(`https://syncora.ai/join/${currentCode}`);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleRegenerateCode = () => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    let rand = "";
    for (let i = 0; i < 4; i++) {
      rand += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setCurrentCode(`NOVA-${rand}`);
  };

  const handleJoinWithCode = (e) => {
    e.preventDefault();
    if (!joinCodeInput.trim()) return;
    setJoinStatus("Joined workspace Nova Studio successfully!");
    setTimeout(() => {
      setJoinStatus(null);
      setJoinCodeInput("");
    }, 2500);
  };

  // Merge currentUser into team display
  let displayList = [...(members || [])];
  if (currentUser?.name) {
    const matchIdx = displayList.findIndex(
      (m) => m.name.toLowerCase() === currentUser.name.toLowerCase()
    );

    if (matchIdx >= 0) {
      displayList[matchIdx] = {
        ...displayList[matchIdx],
        name: currentUser.name,
        title: currentUser.title,
        avatarBg: currentUser.avatarColor || displayList[matchIdx].avatarBg,
        telegramHandle: currentUser.telegram || displayList[matchIdx].telegramHandle,
        isCurrentSession: true,
      };
    } else {
      const customCard = {
        id: "mem-current-session",
        name: currentUser.name,
        initials: currentUser.name
          .split(" ")
          .map((n) => n[0])
          .join("")
          .slice(0, 2)
          .toUpperCase(),
        title: currentUser.title || (currentUser.role === "leader" ? "Team Leader" : "Specialist"),
        role: currentUser.role || "leader",
        avatarBg: currentUser.avatarColor || (currentUser.role === "member" ? "var(--accent-cyan)" : "var(--accent-primary)"),
        online: true,
        activeTasks: 4,
        completionRate: 88,
        workload: 65,
        workloadStatus: "Optimal",
        telegramHandle: currentUser.telegram || "@syncora_user",
        isCurrentSession: true,
      };
      displayList = [customCard, ...displayList];
    }
  }

  return (
    <div>
      {/* Team Member Cards Grid */}
      <div className="team-cards-grid">
        {displayList.map((member) => {
          const isOverloaded = member.workload >= 90;
          const barColor = isOverloaded ? "var(--status-progress)" : "var(--status-completed)";

          return (
            <div key={member.id} className="team-member-card">
              {/* Member Avatar with Online Indicator */}
              <div
                className="member-avatar-large"
                style={{ backgroundColor: member.avatarBg || "var(--accent-primary)" }}
              >
                {member.initials}
                {member.online && <span className="avatar-online-dot" />}
              </div>

              {/* Name & Title */}
              <div className="member-card-name" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
                <span>{member.name}</span>
                {member.isCurrentSession && (
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: "700",
                      color: "var(--accent-primary)",
                      backgroundColor: "var(--accent-primary-bg)",
                      border: "1px solid var(--accent-primary-border)",
                      padding: "1px 6px",
                      borderRadius: "4px",
                    }}
                  >
                    YOU
                  </span>
                )}
              </div>
              <div className="member-card-role">{member.title}</div>
              {member.telegramHandle && (
                <div style={{ fontSize: "11px", color: "var(--accent-cyan)", marginTop: "2px", fontWeight: "500" }}>
                  {member.telegramHandle}
                </div>
              )}

              {/* Active Tasks & Completion Rate */}
              <div className="member-stats-row">
                <div className="member-stat-box" style={{ borderRight: "1px solid var(--border-subtle)" }}>
                  <span className="member-stat-label">ACTIVE TASKS</span>
                  <span className="member-stat-val">{member.activeTasks}</span>
                </div>
                <div className="member-stat-box">
                  <span className="member-stat-label">COMPLETION</span>
                  <span className="member-stat-val">{member.completionRate}%</span>
                </div>
              </div>

              {/* Current Workload Bar */}
              <div className="member-load-section">
                <div className="member-load-header">
                  <span className="member-load-label">Current workload</span>
                  <span className="member-load-percent" style={{ color: isOverloaded ? "var(--status-progress)" : "var(--text-white)" }}>
                    {member.workload}%
                  </span>
                </div>
                <div className="pulse-progress-track">
                  <div
                    className="pulse-progress-fill"
                    style={{
                      width: `${member.workload}%`,
                      backgroundColor: barColor,
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Invite Your Team Access Card (Team Code Center) */}
      <div className="invite-access-card" style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div className="section-label">TEAM ACCESS CODE</div>
            <h2 className="section-title">Invite your team</h2>
            <p className="page-subtitle" style={{ fontSize: "14px", marginTop: "2px" }}>
              Share this secure team code or direct join link with new team members. Expires in 48 hours.
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <div className="code-pill-wrapper">
              <span className="code-text">{currentCode}</span>
              <button
                type="button"
                className="copy-code-btn"
                onClick={handleCopyCode}
                title="Copy secure team code"
              >
                {copiedCode ? (
                  <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--status-completed)" }}>
                    <Check size={14} /> Copied
                  </span>
                ) : (
                  <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <Copy size={14} /> Copy code
                  </span>
                )}
              </button>
            </div>

            <button
              type="button"
              className="btn-secondary"
              onClick={handleCopyLink}
              title="Copy direct invite URL"
              style={{ padding: "8px 12px", fontSize: "13px" }}
            >
              {copiedLink ? (
                <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "var(--status-completed)" }}>
                  <Check size={14} /> Link Copied
                </span>
              ) : (
                <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                  <LinkIcon size={14} /> Copy link
                </span>
              )}
            </button>

            <button
              type="button"
              className="btn-secondary"
              onClick={handleRegenerateCode}
              title="Generate a fresh secure team code"
              style={{ padding: "8px 12px", fontSize: "13px" }}
            >
              <RefreshCw size={14} />
              Regenerate
            </button>
          </div>
        </div>

        {/* Enter Team Code to Join */}
        <div
          style={{
            borderTop: "1px solid var(--border-subtle)",
            paddingTop: "16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "14px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <ShieldCheck size={16} color="var(--accent-primary)" />
            <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
              Have another workspace team code? Enter it below to join.
            </span>
          </div>

          <form onSubmit={handleJoinWithCode} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <input
              type="text"
              placeholder="e.g. NOVA-9X2L"
              value={joinCodeInput}
              onChange={(e) => setJoinCodeInput(e.target.value.toUpperCase())}
              className="form-input"
              style={{
                width: "160px",
                padding: "6px 10px",
                fontSize: "12px",
                fontFamily: "var(--font-mono)",
                textTransform: "uppercase",
              }}
            />
            <button
              type="submit"
              className="btn-primary"
              style={{ padding: "6px 14px", fontSize: "12px", display: "inline-flex", alignItems: "center", gap: "5px" }}
            >
              <UserPlus size={13} />
              Join Team
            </button>
          </form>
        </div>

        {joinStatus && (
          <div
            style={{
              padding: "8px 12px",
              backgroundColor: "var(--status-completed-bg)",
              border: "1px solid var(--status-completed-border)",
              borderRadius: "8px",
              color: "var(--status-completed)",
              fontSize: "13px",
              fontWeight: "600",
            }}
          >
            ✓ {joinStatus}
          </div>
        )}
      </div>
    </div>
  );
}
