import React, { useState } from "react";
import { X, AlertTriangle, Send } from "lucide-react";

export function ReportBlockerModal({ isOpen, onClose, tasks = [], onReportBlocker }) {
  const [selectedTaskId, setSelectedTaskId] = useState(tasks?.[0]?.id || "");
  const [reason, setReason] = useState("");
  const [urgency, setUrgency] = useState("Critical");
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) return;

    setSubmitting(true);
    try {
      await onReportBlocker(selectedTaskId, reason, urgency);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span style={{ fontSize: "11px", fontWeight: "700", color: "var(--status-blocked)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
              Blocker Detection
            </span>
            <h3 className="card-title" style={{ marginTop: "4px", display: "flex", alignItems: "center", gap: "8px" }}>
              <AlertTriangle size={18} color="var(--status-blocked)" />
              Report Blocker
            </h3>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Select Blocked Task</label>
            <select
              className="form-select"
              value={selectedTaskId}
              onChange={(e) => setSelectedTaskId(e.target.value)}
            >
              {(tasks || []).map((t) => (
                <option key={t.id} value={t.id}>
                  {t.id} — {t.title} ({t.status})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Urgency Level</label>
            <select
              className="form-select"
              value={urgency}
              onChange={(e) => setUrgency(e.target.value)}
            >
              <option value="Critical">Critical (Immediate Leader Attention)</option>
              <option value="High">High (Impacting today's deliverable)</option>
              <option value="Medium">Medium (Impacting upcoming milestone)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Blocker Details & Missing Dependencies</label>
            <textarea
              className="form-textarea"
              placeholder="Describe what is blocking you (e.g., credentials, code review, third party API outage)..."
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>

          <div
            style={{
              padding: "10px 14px",
              backgroundColor: "var(--accent-primary-bg)",
              border: "1px solid var(--accent-primary-border)",
              borderRadius: "8px",
              fontSize: "12px",
              color: "var(--accent-primary)",
              marginBottom: "18px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Send size={15} />
            <span>Syncora AI will broadcast this blocker to the team Telegram channel immediately.</span>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-danger"
              disabled={submitting}
              style={{
                backgroundColor: "var(--status-blocked)",
                color: "#FFFFFF",
                boxShadow: "0 0 10px var(--status-blocked-glow)",
              }}
            >
              {submitting ? (
                <>
                  <span className="status-ring-spinner" style={{ borderColor: "#FFFFFF", borderTopColor: "transparent" }} />
                  Broadcasting...
                </>
              ) : (
                "Report Blocker"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
