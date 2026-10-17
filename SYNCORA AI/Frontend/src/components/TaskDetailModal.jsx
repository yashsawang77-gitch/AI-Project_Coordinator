import React, { useState } from "react";
import { X, CheckCircle2, Clock, AlertTriangle, User, Calendar, Tag, FileText } from "lucide-react";

export function TaskDetailModal({ isOpen, onClose, task, onStatusChange }) {
  if (!isOpen || !task) return null;

  const [currentStatus, setCurrentStatus] = useState(task.status);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleStatusUpdate = async (newStatus) => {
    setIsUpdating(true);
    setCurrentStatus(newStatus);
    if (onStatusChange) {
      await onStatusChange(task.id, newStatus);
    }
    setTimeout(() => {
      setIsUpdating(false);
      onClose();
    }, 400);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" style={{ maxWidth: "600px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span className="kbd-badge">{task.id}</span>
              <span className="meta-text">{task.project}</span>
            </div>
            <h3 className="card-title" style={{ fontSize: "20px", marginTop: "6px" }}>
              {task.title}
            </h3>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Task Properties Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "14px",
            backgroundColor: "#111a2d",
            borderRadius: "12px",
            padding: "16px",
            marginBottom: "20px",
          }}
        >
          <div>
            <div className="meta-text" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <User size={14} /> Assignee
            </div>
            <div style={{ fontSize: "15px", fontWeight: "600", color: "#fff", marginTop: "4px" }}>
              {task.assignee || "Unassigned"}
            </div>
          </div>

          <div>
            <div className="meta-text" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Calendar size={14} /> Deadline
            </div>
            <div style={{ fontSize: "15px", fontWeight: "600", color: "#fff", marginTop: "4px" }}>
              {task.deadline || "None"}
            </div>
          </div>

          <div>
            <div className="meta-text" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Clock size={14} /> Estimated Effort
            </div>
            <div style={{ fontSize: "15px", fontWeight: "600", color: "#fff", marginTop: "4px" }}>
              {task.estimatedHours || "N/A"}
            </div>
          </div>

          <div>
            <div className="meta-text" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Tag size={14} /> Priority
            </div>
            <div
              style={{
                fontSize: "14px",
                fontWeight: "700",
                marginTop: "4px",
                color: task.priority === "Critical" ? "var(--status-blocked)" : "var(--status-completed)",
              }}
            >
              {task.priority || "Medium"}
            </div>
          </div>
        </div>

        {/* Description / Telegram Context */}
        <div style={{ marginBottom: "22px" }}>
          <div className="meta-text" style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
            <FileText size={14} /> Deliverable Context & Scope
          </div>
          <p style={{ fontSize: "14px", color: "#cbd5e1", lineHeight: "1.5" }}>
            {task.description || "Tracked through automated Syncora AI Telegram check-ins."}
          </p>
          {task.blockerReason && (
            <div
              style={{
                marginTop: "12px",
                padding: "10px 14px",
                backgroundColor: "rgba(245, 158, 11, 0.1)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                borderRadius: "8px",
                fontSize: "13px",
                color: "#fbbf24",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <AlertTriangle size={16} />
              <span>Blocker Detail: {task.blockerReason}</span>
            </div>
          )}
        </div>

        {/* Change Status Fast Actions */}
        <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "18px" }}>
          <div className="meta-text" style={{ marginBottom: "10px" }}>
            Update Task Status:
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button
              type="button"
              className={`filter-tab ${currentStatus === "In Progress" ? "active" : ""}`}
              onClick={() => handleStatusUpdate("In Progress")}
              disabled={isUpdating}
            >
              In Progress
            </button>
            <button
              type="button"
              className={`filter-tab ${currentStatus === "Blocked" ? "active" : ""}`}
              style={{ color: currentStatus === "Blocked" ? "#fbbf24" : undefined }}
              onClick={() => handleStatusUpdate("Blocked")}
              disabled={isUpdating}
            >
              Blocked
            </button>
            <button
              type="button"
              className={`filter-tab ${currentStatus === "Completed" ? "active" : ""}`}
              style={{ color: currentStatus === "Completed" ? "#10b981" : undefined }}
              onClick={() => handleStatusUpdate("Completed")}
              disabled={isUpdating}
            >
              Completed
            </button>
            <button
              type="button"
              className={`filter-tab ${currentStatus === "Pending" ? "active" : ""}`}
              onClick={() => handleStatusUpdate("Pending")}
              disabled={isUpdating}
            >
              Pending
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

