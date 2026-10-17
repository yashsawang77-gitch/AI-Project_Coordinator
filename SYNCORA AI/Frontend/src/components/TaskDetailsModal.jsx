import React, { useState, useEffect } from "react";
import {
  X,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Calendar,
  User,
} from "lucide-react";

export function TaskDetailsModal({
  isOpen,
  onClose,
  task,
  onUpdateStatus,
  onOpenReportBlocker,
  members = [],
}) {
  if (!isOpen || !task) return null;

  const [status, setStatus] = useState(task.status || "In Progress");
  const [priority, setPriority] = useState(task.priority || "High");
  const [assignee, setAssignee] = useState(task.assignee || "Alex Morgan");
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    if (task) {
      setStatus(task.status || "In Progress");
      setPriority(task.priority || "High");
      setAssignee(task.assignee || "Alex Morgan");
    }
  }, [task]);

  const handleSaveStatus = async (newStatus) => {
    setIsUpdating(true);
    try {
      await onUpdateStatus(task.id, newStatus || status);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsUpdating(false);
    }
  };

  const isCompleted = status === "Completed";
  const isBlocked = status === "Blocked";

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-container"
        style={{ maxWidth: "560px" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span className="code-text" style={{ fontSize: "12px", color: "var(--accent-primary)" }}>
                {task.id}
              </span>
              <span className="kbd-badge">{task.project || "Product Core"}</span>
            </div>
            <h3
              className="card-title"
              style={{ fontSize: "18px", marginTop: "6px", lineHeight: "1.3" }}
            >
              {task.title}
            </h3>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Status & Priority Ribbon */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "14px",
            backgroundColor: "var(--bg-app)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "10px",
            padding: "12px 16px",
            marginBottom: "18px",
          }}
        >
          <div>
            <div className="meta-text" style={{ fontSize: "11px", marginBottom: "4px" }}>
              CURRENT STATUS
            </div>
            <select
              className="form-select"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              style={{ padding: "7px 10px", fontSize: "13px" }}
            >
              <option value="In Progress">In Progress</option>
              <option value="Completed">Completed</option>
              <option value="Blocked">Blocked</option>
              <option value="Pending">Pending</option>
            </select>
          </div>

          <div>
            <div className="meta-text" style={{ fontSize: "11px", marginBottom: "4px" }}>
              PRIORITY LEVEL
            </div>
            <select
              className="form-select"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              style={{ padding: "7px 10px", fontSize: "13px" }}
            >
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
        </div>

        {/* Task Details List */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "18px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingBottom: "8px",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <span className="meta-text" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <User size={14} color="var(--text-muted)" /> Assignee
            </span>
            <span style={{ color: "var(--text-white)", fontWeight: "600", fontSize: "13px" }}>
              {assignee}
            </span>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingBottom: "8px",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <span className="meta-text" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Calendar size={14} color="var(--text-muted)" /> Deadline
            </span>
            <span
              style={{
                color: task.deadline?.toLowerCase().includes("overdue") ? "var(--status-blocked)" : "var(--text-white)",
                fontWeight: "600",
                fontSize: "13px",
              }}
            >
              {task.deadline || "Tomorrow, 5:00 PM"}
            </span>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingBottom: "8px",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <span className="meta-text" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Clock size={14} color="var(--text-muted)" /> Estimated Effort
            </span>
            <span style={{ color: "var(--text-white)", fontWeight: "600", fontSize: "13px" }}>
              {task.estimatedHours || "6-10h"}
            </span>
          </div>

          {task.description && (
            <div style={{ marginTop: "4px" }}>
              <span className="meta-text" style={{ fontSize: "11px" }}>Notes / Context:</span>
              <p
                style={{
                  fontSize: "13px",
                  color: "var(--text-secondary)",
                  marginTop: "4px",
                  backgroundColor: "var(--bg-app)",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  border: "1px solid var(--border-subtle)",
                  lineHeight: "1.4",
                }}
              >
                {task.description}
              </p>
            </div>
          )}
        </div>

        {/* Quick Action Buttons */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "18px" }}>
          {!isCompleted ? (
            <button
              type="button"
              className="btn-secondary"
              style={{
                flex: 1,
                borderColor: "var(--status-completed-border)",
                color: "var(--status-completed)",
                backgroundColor: "var(--status-completed-bg)",
                justifyContent: "center",
              }}
              onClick={() => handleSaveStatus("Completed")}
            >
              <CheckCircle2 size={15} /> Mark as Complete
            </button>
          ) : (
            <button
              type="button"
              className="btn-secondary"
              style={{
                flex: 1,
                justifyContent: "center",
              }}
              onClick={() => handleSaveStatus("In Progress")}
            >
              Reopen Task
            </button>
          )}

          {!isBlocked && (
            <button
              type="button"
              className="btn-secondary"
              style={{
                borderColor: "var(--status-blocked-border)",
                color: "var(--status-blocked)",
                backgroundColor: "var(--status-blocked-bg)",
                justifyContent: "center",
              }}
              onClick={() => {
                onClose();
                if (onOpenReportBlocker) onOpenReportBlocker(task);
              }}
            >
              <AlertTriangle size={15} /> Report Blocker
            </button>
          )}
        </div>

        {/* Footer Save & Cancel */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
          <button type="button" className="btn-secondary" onClick={onClose} disabled={isUpdating}>
            Close
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={isUpdating}
            onClick={() => handleSaveStatus(status)}
          >
            {isUpdating ? "Saving..." : "Save Status"}
          </button>
        </div>
      </div>
    </div>
  );
}
