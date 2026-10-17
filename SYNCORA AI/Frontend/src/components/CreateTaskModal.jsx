import React, { useState } from "react";
import { X, Plus, Sparkles } from "lucide-react";

export function CreateTaskModal({ isOpen, onClose, onCreateTask, members = [] }) {
  const [formData, setFormData] = useState({
    title: "",
    project: "Product Core",
    assignee: "Alex Morgan",
    deadline: "Tomorrow",
    priority: "High",
    estimatedHours: "8-12h",
    description: "",
  });

  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) return;

    setLoading(true);
    try {
      await onCreateTask(formData);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 className="card-title" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Plus size={18} color="var(--accent-primary)" />
              Create Task
            </h3>
            <p className="meta-text" style={{ marginTop: "2px" }}>
              Syncora will track progress and coordinate updates via Telegram.
            </p>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Task Title</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Implement webhook retry mechanism"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
            <div className="form-group">
              <label className="form-label">Project</label>
              <select
                className="form-select"
                value={formData.project}
                onChange={(e) => setFormData({ ...formData, project: e.target.value })}
              >
                <option value="Product Core">Product Core</option>
                <option value="Infrastructure">Infrastructure</option>
                <option value="Marketing Launch">Marketing Launch</option>
                <option value="Growth">Growth</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Assignee</label>
              <select
                className="form-select"
                value={formData.assignee}
                onChange={(e) => setFormData({ ...formData, assignee: e.target.value })}
              >
                {members.map((m) => (
                  <option key={m.id} value={m.name}>
                    {m.name} ({m.title})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
            <div className="form-group">
              <label className="form-label">Deadline</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., Tomorrow, 5:00 PM"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Priority</label>
              <select
                className="form-select"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Description & Telegram Context</label>
            <textarea
              className="form-textarea"
              placeholder="Provide context or key deliverables for AI follow-up parsing..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "24px" }}>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? (
                <>
                  <span className="status-ring-spinner" /> Creating...
                </>
              ) : (
                <>
                  <Sparkles size={16} /> Create Task
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

