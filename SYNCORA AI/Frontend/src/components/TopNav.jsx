import React, { useState } from "react";
import {
  Search,
  Bell,
  LogOut,
  ArrowLeftRight,
  User,
  Shield,
  Check,
  Sun,
  Moon,
  Send,
  Zap,
} from "lucide-react";

export function TopNav({
  category = "COMMAND CENTER",
  title,
  subtitle,
  searchQuery,
  setSearchQuery,
  currentRole,
  currentUser,
  toggleRole,
  onLogout,
  theme = "light",
  toggleTheme,
}) {
  const isLeader = currentRole === "leader";
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showPingDetail, setShowPingDetail] = useState(false);

  const initials = currentUser?.name
    ? currentUser.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : isLeader
    ? "MC"
    : "AM";

  const userName = currentUser?.name || (isLeader ? "Maya Chen" : "Alex Morgan");
  const userTitle = currentUser?.title || (isLeader ? "Team Leader" : "Product Designer");
  const userEmail = currentUser?.email || (isLeader ? "maya.chen@novastudio.ai" : "alex.m@novastudio.ai");

  return (
    <header className="top-header-wrapper">
      {/* Title & Category Column */}
      <div>
        <div className="section-label">{category}</div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>

      {/* Right Tools: Live Status Pill, Search, Theme Toggle, Notification, Profile */}
      <div className="header-tools">
        {/* Live Integration Status Pill in Top Header */}
        <div
          className="status-pill-telegram"
          title="Click to check Telegram bot latency"
          onClick={() => setShowPingDetail(!showPingDetail)}
          style={{ cursor: "pointer" }}
        >
          <span className="live-indicator-dot" />
          <span className="status-pill-text">🟢 Telegram Bot: Connected</span>
          <span className="status-pill-ping">42ms</span>
        </div>

        {/* Search Input Box */}
        <div className="search-input-box">
          <Search size={15} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search anything..."
            value={searchQuery || ""}
            onChange={(e) => setSearchQuery && setSearchQuery(e.target.value)}
          />
          <span className="kbd-badge">⌘ K</span>
        </div>

        {/* Visible Theme Toggle Switch (Sun / Moon) */}
        <button
          type="button"
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title={theme === "light" ? "Switch to Dark mode" : "Switch to Light mode"}
          aria-label="Toggle theme mode"
        >
          {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
        </button>

        {/* Notifications Icon Button */}
        <div style={{ position: "relative" }}>
          <button
            type="button"
            className="icon-btn"
            title="Syncora AI notifications"
            aria-label="Notifications"
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowProfileMenu(false);
            }}
          >
            <Bell size={17} />
            <span className="notification-dot" />
          </button>

          {showNotifications && (
            <div
              style={{
                position: "absolute",
                top: "46px",
                right: "0",
                width: "320px",
                backgroundColor: "var(--bg-card-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "12px",
                boxShadow: "var(--shadow-dropdown)",
                padding: "16px",
                zIndex: 300,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <span style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-white)" }}>AI Notifications</span>
                <span className="kbd-badge" style={{ color: "var(--accent-primary)" }}>3 New</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ padding: "8px 10px", backgroundColor: "var(--bg-card)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--status-progress)" }}>Blocker Detected in Telegram</div>
                  <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px" }}>Elena flagged API latency in #core-backend</div>
                </div>
                <div style={{ padding: "8px 10px", backgroundColor: "var(--bg-card)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--status-completed)" }}>Workload Alert Resolved</div>
                  <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px" }}>Reassignment proposal approved for Maya Chen</div>
                </div>
                <div style={{ padding: "8px 10px", backgroundColor: "var(--bg-card)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--accent-cyan)" }}>Telegram Bot Active</div>
                  <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px" }}>Synced 42 status events in the last 2 hours</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Avatar with Interactive Dropdown */}
        <div style={{ position: "relative" }}>
          <div
            className="header-avatar"
            style={{
              backgroundColor: currentUser?.avatarColor || (isLeader ? "#6366F1" : "#06B6D4"),
              cursor: "pointer",
            }}
            title={`${userName} (${isLeader ? "Leader" : "Member"})`}
            onClick={() => {
              setShowProfileMenu(!showProfileMenu);
              setShowNotifications(false);
            }}
          >
            {initials}
          </div>

          {showProfileMenu && (
            <div
              style={{
                position: "absolute",
                top: "46px",
                right: "0",
                width: "290px",
                backgroundColor: "var(--bg-card-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "14px",
                boxShadow: "var(--shadow-dropdown)",
                padding: "16px",
                zIndex: 300,
              }}
            >
              {/* Profile Card Header */}
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "10px",
                    backgroundColor: currentUser?.avatarColor || (isLeader ? "#6366F1" : "#06B6D4"),
                    color: "#fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: "800",
                    fontSize: "14px",
                  }}
                >
                  {initials}
                </div>
                <div>
                  <div style={{ fontSize: "15px", fontWeight: "700", color: "var(--text-white)" }}>
                    {userName}
                  </div>
                  <div style={{ fontSize: "12px", color: isLeader ? "var(--accent-primary)" : "var(--accent-cyan)", fontWeight: "600" }}>
                    {userTitle}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {userEmail}
                  </div>
                </div>
              </div>

              {/* Profile Filled Details Panel */}
              <div
                style={{
                  backgroundColor: "var(--bg-app)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "10px 12px",
                  marginBottom: "12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                  fontSize: "12px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-muted)" }}>Workspace:</span>
                  <span style={{ fontWeight: "600", color: "var(--text-white)" }}>{currentUser?.workspace || "Nova Studio"}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-muted)" }}>Telegram:</span>
                  <span style={{ fontWeight: "600", color: "var(--accent-cyan)" }}>{currentUser?.telegram || (isLeader ? "@maya_syncora" : "@alex_dev")}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-muted)" }}>Capacity:</span>
                  <span style={{ fontWeight: "600", color: "var(--status-completed)" }}>{currentUser?.capacity ? `${currentUser.capacity} hrs/wk` : "35 hrs/wk"}</span>
                </div>
                {currentUser?.skills && (
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <span style={{ color: "var(--text-muted)" }}>Skills:</span>
                    <span
                      style={{
                        fontWeight: "500",
                        color: "var(--text-secondary)",
                        maxWidth: "160px",
                        textAlign: "right",
                        fontSize: "11px",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                      title={currentUser.skills}
                    >
                      {currentUser.skills}
                    </span>
                  </div>
                )}
              </div>

              <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "8px", display: "flex", flexDirection: "column", gap: "4px" }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowProfileMenu(false);
                    if (toggleRole) toggleRole();
                  }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    background: "none",
                    border: "none",
                    color: "var(--text-primary)",
                    fontSize: "13px",
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--bg-sidebar-active)")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                >
                  <ArrowLeftRight size={14} color="var(--accent-primary)" />
                  <span>Switch to {isLeader ? "Member Dashboard" : "Leader Dashboard"}</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setShowProfileMenu(false);
                    if (onLogout) onLogout();
                  }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    background: "none",
                    border: "none",
                    color: "var(--status-blocked)",
                    fontSize: "13px",
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--status-blocked-bg)")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                >
                  <LogOut size={14} color="var(--status-blocked)" />
                  <span>Sign Out to Login Page</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
