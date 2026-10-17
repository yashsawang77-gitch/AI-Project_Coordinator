import React from "react";
import { ChevronRight, AlertCircle, CheckCircle2, Clock } from "lucide-react";

export function TaskRow({ task, onClick, onStatusChange }) {
  const getStatusColor = () => {
    switch (task.status) {
      case "Completed":
        return "#10B981"; // Emerald Green
      case "In Progress":
        return "#F59E0B"; // Amber
      case "Blocked":
        return "#EF4444"; // Bright Crimson Red
      case "Pending":
      default:
        return "#64748B"; // Slate Gray
    }
  };

  const statusColor = getStatusColor();

  const renderStatusBadge = () => {
    switch (task.status) {
      case "In Progress":
        return (
          <span className="status-badge in-progress">
            <span className="status-ring-spinner" />
            In Progress
          </span>
        );
      case "Blocked":
        return (
          <span className="status-badge blocked">
            <AlertCircle size={13} />
            Blocked
          </span>
        );
      case "Completed":
        return (
          <span className="status-badge completed">
            <CheckCircle2 size={13} />
            Completed
          </span>
        );
      case "Pending":
      default:
        return (
          <span className="status-badge pending">
            <Clock size={12} />
            Pending
          </span>
        );
    }
  };

  const isOverdue = task.deadline && task.deadline.toLowerCase().includes("overdue");

  return (
    <div className="task-row" onClick={() => onClick && onClick(task)}>
      {/* Task Info Column */}
      <div className="task-info-col">
        <div
          className="task-accent-bar"
          style={{ backgroundColor: statusColor }}
        />
        <div>
          <div className="task-title">{task.title}</div>
          <div className="task-meta">
            <span className="task-id-badge">{task.id}</span>
            <span className="team-code-pill" title="Assigned Team Code">
              {task.teamCode || (task.project === "Infrastructure" ? "NOVA-INFRA" : task.project === "Marketing Launch" ? "NOVA-MKTG" : task.project === "Growth" ? "NOVA-GRW" : "NOVA-CORE")}
            </span>
            <span className="task-project-sep">·</span>
            <span className="task-project-text">{task.project}</span>
          </div>
        </div>
      </div>

      {/* Assignee Column */}
      <div className="assignee-col">
        <div
          className="assignee-avatar"
          style={{
            backgroundColor: task.assigneeBg || "var(--accent-primary-bg)",
            color: task.assigneeTextColor || "var(--accent-primary)",
            borderColor: "var(--border-subtle)",
          }}
        >
          {task.assigneeInitials || (task.assignee ? task.assignee.substring(0, 2).toUpperCase() : "UN")}
        </div>
        <span className="assignee-name">{task.assignee || "Unassigned"}</span>
      </div>

      {/* Deadline Column */}
      <div className={`deadline-col ${isOverdue ? "overdue" : ""}`}>
        {task.deadline || "No deadline"}
      </div>

      {/* Status Column */}
      <div>
        {renderStatusBadge()}
      </div>

      {/* Action Arrow */}
      <div style={{ display: "flex", justifyContent: "flex-end", color: "var(--text-muted)" }}>
        <ChevronRight size={16} />
      </div>
    </div>
  );
}
