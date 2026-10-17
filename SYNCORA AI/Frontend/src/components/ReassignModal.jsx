import React, { useState } from "react";
import { X, ArrowRight, ShieldAlert, AlertTriangle } from "lucide-react";

export function ReassignModal({ isOpen, onClose, recommendation, onApprove, onReject }) {
  const [submitting, setSubmitting] = useState(false);
  const [leaderNote, setLeaderNote] = useState("");

  if (!isOpen || !recommendation) return null;

  const handleApprove = async () => {
    setSubmitting(true);
    try {
      await onApprove(recommendation.id, leaderNote);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = () => {
    if (onReject) onReject(recommendation.id);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" style={{ maxWidth: "600px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span
              style={{
                fontSize: "11px",
                fontWeight: "700",
                color: "var(--status-blocked)",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
              }}
            >
              {recommendation.priority} Workload Rebalance
            </span>
            <h3 className="card-title" style={{ marginTop: "4px", display: "flex", alignItems: "center", gap: "8px" }}>
              <ShieldAlert size={18} color="var(--status-blocked)" />
              Review AI Reassignment Proposal
            </h3>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Member Transfer Comparison */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr auto 1fr",
            alignItems: "center",
            gap: "14px",
            backgroundColor: "var(--bg-app)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "10px",
            padding: "14px 18px",
            marginBottom: "18px",
          }}
        >
          <div>
            <div className="meta-text">Current Assignee (Overloaded)</div>
            <div style={{ fontSize: "15px", fontWeight: "700", color: "var(--text-white)", marginTop: "2px" }}>
              {recommendation.overburdenedMember}
            </div>
            <div style={{ fontSize: "13px", color: "var(--status-blocked)", fontWeight: "600", marginTop: "2px" }}>
              Load: {recommendation.currentLoad}%
            </div>
          </div>

          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "var(--accent-primary-bg)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--accent-primary)",
            }}
          >
            <ArrowRight size={16} />
          </div>

          <div>
            <div className="meta-text">Target Assignee (Available)</div>
            <div style={{ fontSize: "15px", fontWeight: "700", color: "var(--text-white)", marginTop: "2px" }}>
              {recommendation.suggestedMember}
            </div>
            <div style={{ fontSize: "13px", color: "var(--status-completed)", fontWeight: "600", marginTop: "2px" }}>
              Current Load: {recommendation.suggestedLoad}%
            </div>
          </div>
        </div>

        {/* Task Details */}
        <div
          style={{
            backgroundColor: "var(--bg-app)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "10px",
            padding: "14px 18px",
            marginBottom: "16px",
          }}
        >
          <div className="meta-text">Target Task for Redistribution</div>
          <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text-white)", marginTop: "4px" }}>
            {recommendation.taskToReassign.id} · {recommendation.taskToReassign.title}
          </div>
          <div style={{ display: "flex", gap: "16px", marginTop: "6px", fontSize: "13px", color: "var(--text-secondary)" }}>
            <span>
              Estimated Effort: <strong style={{ color: "var(--text-white)" }}>{recommendation.taskToReassign.estimatedHours}</strong>
            </span>
            <span>
              Confidence: <strong style={{ color: "var(--accent-primary)" }}>{recommendation.taskToReassign.confidence}</strong>
            </span>
          </div>
        </div>

        {/* AI Rationale */}
        <div style={{ marginBottom: "18px" }}>
          <div className="meta-text" style={{ marginBottom: "4px" }}>AI Equilibrium Rationale:</div>
          <p
            style={{
              fontSize: "13px",
              color: "var(--text-secondary)",
              lineHeight: "1.45",
              backgroundColor: "var(--bg-app)",
              padding: "12px 14px",
              borderRadius: "8px",
              border: "1px solid var(--border-subtle)",
            }}
          >
            {recommendation.reasoning}
          </p>
        </div>

        {/* Leader Note Input */}
        <div className="form-group" style={{ marginBottom: "20px" }}>
          <label className="form-label">Approval Note / Handover Context (Optional)</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g., Reviewed in standup, safe to reassign to keep sprint on track..."
            value={leaderNote}
            onChange={(e) => setLeaderNote(e.target.value)}
          />
        </div>

        {/* Actions */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
          <button type="button" className="btn-secondary" onClick={handleReject} disabled={submitting}>
            Dismiss
          </button>
          <button type="button" className="btn-primary" onClick={handleApprove} disabled={submitting}>
            {submitting ? "Applying Reassignment..." : "Approve Workload Rebalance"}
          </button>
        </div>
      </div>
    </div>
  );
}
