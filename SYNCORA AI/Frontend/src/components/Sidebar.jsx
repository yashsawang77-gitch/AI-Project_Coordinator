import React from "react";
import {
  LayoutGrid,
  CheckSquare,
  Users,
  Sparkles,
  TrendingUp,
  Activity,
  Link2,
  Settings,
  ChevronRight,
  Sparkle,
  ArrowLeftRight,
  LogOut,
  Send,
  AlertTriangle,
} from "lucide-react";

export function Sidebar({
  activeNav,
  setActiveNav,
  currentRole,
  toggleRole,
  onOpenCreateTask,
  onOpenReportBlocker,
  currentUser,
  onLogout,
}) {
  const isLeader = currentRole === "leader";

  // Navigation configurations for Leader and Member
  const leaderNavItems = [
    { id: "overview", label: "Overview", icon: LayoutGrid },
    { id: "tasks", label: "All Tasks", icon: CheckSquare },
    { id: "team", label: "Team", icon: Users },
    { id: "ai-activity", label: "AI Activity", icon: Sparkles, badge: "8" },
    { id: "analytics", label: "Analytics", icon: TrendingUp },
    { id: "workload", label: "AI Workload", icon: Activity },
    { id: "integrations", label: "Integrations", icon: Link2 },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  const memberNavItems = [
    { id: "member-dashboard", label: "My Dashboard", icon: LayoutGrid },
    { id: "tasks", label: "My Tasks", icon: CheckSquare },
    { id: "team", label: "Team Overview", icon: Users },
    { id: "ai-activity", label: "AI Updates", icon: Sparkles },
    { id: "workload", label: "My Workload", icon: Activity },
    { id: "integrations", label: "Telegram Bot", icon: Send },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  const currentNavItems = isLeader ? leaderNavItems : memberNavItems;

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

  return (
    <aside className="sidebar">
      <div className="sidebar-scroll">
        {/* Brand Header */}
        <div className="sidebar-logo">
          <div className="logo-icon-wrap">
            <svg width="18" height="18" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M6 10C6 7.79086 7.79086 6 10 6H18C20.2091 6 22 7.79086 22 10L14 18H10C7.79086 18 6 16.2091 6 14V10Z"
                fill="var(--accent-primary)"
              />
              <path
                d="M10 22C10 19.7909 11.7909 18 14 18H22C24.2091 18 26 19.7909 26 22V26C26 28.2091 24.2091 30 22 30H14C11.7909 30 10 28.2091 10 26V22Z"
                fill="var(--accent-primary)"
                fillOpacity="0.75"
              />
            </svg>
          </div>
          <span className="logo-text">
            syncora <span className="logo-badge">AI</span>
          </span>
        </div>

        {/* Workspace Selector */}
        <div className="workspace-selector">
          <div className="workspace-info">
            <div className="workspace-avatar" style={{ backgroundColor: currentUser?.avatarColor || "var(--accent-primary)" }}>
              {currentUser?.workspace ? currentUser.workspace[0].toUpperCase() : "N"}
            </div>
            <div className="workspace-text">
              <span className="workspace-tag">WORKSPACE</span>
              <span className="workspace-name">{currentUser?.workspace || "Nova Studio"}</span>
            </div>
          </div>
          <ChevronRight size={14} color="var(--text-muted)" />
        </div>

        {/* Workspace Navigation Group */}
        <div className="sidebar-nav-group">
          <div className="nav-group-label">WORKSPACE</div>
          <nav>
            {currentNavItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = activeNav === item.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  className={`nav-link ${isActive ? "active" : ""}`}
                  onClick={() => setActiveNav(item.id)}
                  style={{ width: "100%", background: "none", textAlign: "left" }}
                >
                  <div className="nav-link-left">
                    <IconComponent size={18} color={isActive ? "var(--accent-primary)" : "currentColor"} />
                    <span className="nav-link-text">{item.label}</span>
                  </div>
                  {item.badge && <span className="nav-badge">{item.badge}</span>}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Sidebar Footer Controls */}
      <div className="sidebar-footer">
        {/* System Operational Status Box */}
        <div className="system-status-box">
          <div className="status-icon-glow">
            <Sparkle size={14} />
          </div>
          <div>
            <div className="status-info-title">Syncora AI</div>
            <div className="status-indicator">
              <span className="status-dot-pulse" />
              <span>Systems operational</span>
            </div>
          </div>
        </div>

        {/* Role Switcher Pill */}
        <button
          type="button"
          className="role-switcher-btn"
          onClick={toggleRole}
          title="Switch view between Leader and Member dashboards"
        >
          <ArrowLeftRight size={13} />
          <span>Switch to {isLeader ? "Member Dashboard" : "Leader Dashboard"}</span>
        </button>

        {/* User Profile Bar */}
        <div className="user-profile-bar">
          <div className="user-profile-left">
            <div
              className="user-avatar"
              style={{
                backgroundColor: currentUser?.avatarColor || (isLeader ? "#6366F1" : "#06B6D4"),
              }}
            >
              {initials}
            </div>
            <div>
              <div className="user-name">{userName}</div>
              <div className="user-role-label">{userTitle} {currentUser?.telegram ? `(${currentUser.telegram})` : ""}</div>
            </div>
          </div>
          <button
            type="button"
            onClick={onLogout}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              padding: "4px",
              borderRadius: "4px",
              transition: "color 0.15s",
            }}
            title="Log Out to Login Page"
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--status-blocked)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  );
}
