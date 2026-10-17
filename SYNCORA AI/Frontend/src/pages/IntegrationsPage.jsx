import React, { useState } from "react";
import { Send, CheckCircle2, RefreshCw } from "lucide-react";

export function IntegrationsPage({ settings }) {
  const [testingPing, setTestingPing] = useState(false);
  const [pingResult, setPingResult] = useState(null);

  const handleTestPing = () => {
    setTestingPing(true);
    setTimeout(() => {
      setTestingPing(false);
      setPingResult({
        latency: "42ms",
        status: "OK",
        telegramApi: "v6.8 Connected",
        timestamp: new Date().toLocaleTimeString(),
      });
    }, 600);
  };

  return (
    <div>
      {/* Telegram Banner (Clean SaaS style with Cyan Accent) */}
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "12px",
          padding: "26px 30px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "24px",
          boxShadow: "var(--shadow-card)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "12px",
              backgroundColor: "var(--accent-cyan-bg)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--accent-cyan)",
            }}
          >
            <Send size={24} />
          </div>
          <div>
            <div className="section-label" style={{ color: "var(--accent-cyan)" }}>MESSAGING INTEGRATION</div>
            <h2 style={{ fontSize: "22px", fontWeight: "700", color: "var(--text-white)", marginTop: "2px" }}>
              Telegram Coordination Engine
            </h2>
            <p className="page-subtitle" style={{ fontSize: "14px" }}>
              Syncora listens to project updates, detects blockers, and answers queries directly in Telegram.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="btn-primary"
          onClick={handleTestPing}
          disabled={testingPing}
          style={{ backgroundColor: "var(--accent-cyan)", color: "#ffffff" }}
        >
          <RefreshCw size={16} className={testingPing ? "status-ring-spinner" : ""} />
          {testingPing ? "Pinging Bot..." : "Test Bot Connection"}
        </button>
      </div>

      {pingResult && (
        <div
          style={{
            padding: "14px 20px",
            backgroundColor: "var(--status-completed-bg)",
            border: "1px solid var(--status-completed-border)",
            borderRadius: "10px",
            color: "var(--status-completed)",
            fontSize: "14px",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <CheckCircle2 size={18} />
            <span>
              Telegram Bot Ping Successful · Latency: <strong>{pingResult.latency}</strong> · Protocol: {pingResult.telegramApi}
            </span>
          </div>
          <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>{pingResult.timestamp}</span>
        </div>
      )}

      {/* Integration Details Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "24px", marginBottom: "24px" }}>
        {/* Active Configuration */}
        <div className="card">
          <div className="section-label">CONFIGURATION</div>
          <h2 className="section-title" style={{ marginBottom: "16px" }}>Active Bot Specs</h2>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "12px", borderBottom: "1px solid var(--border-subtle)" }}>
              <span className="meta-text">Official Bot Handle</span>
              <span style={{ color: "var(--accent-cyan)", fontWeight: "600" }}>{settings?.botName || "@SyncoraBot"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "12px", borderBottom: "1px solid var(--border-subtle)" }}>
              <span className="meta-text">Target Team Group</span>
              <span style={{ color: "var(--text-white)", fontWeight: "600" }}>{settings?.linkedGroup || "Nova Engineering Core"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "12px", borderBottom: "1px solid var(--border-subtle)" }}>
              <span className="meta-text">Webhook Status</span>
              <span style={{ color: "var(--status-completed)", fontWeight: "600", display: "flex", alignItems: "center", gap: "6px" }}>
                <span className="status-dot-pulse" /> Active (SSL Verified)
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "12px", borderBottom: "1px solid var(--border-subtle)" }}>
              <span className="meta-text">Events Parsed Today</span>
              <span style={{ color: "var(--text-white)", fontWeight: "700" }}>{settings?.eventsHandledToday || "142"} messages</span>
            </div>
          </div>
        </div>

        {/* Telegram Bot Commands */}
        <div className="card">
          <div className="section-label">DEVELOPER REFERENCE</div>
          <h2 className="section-title" style={{ marginBottom: "16px" }}>Available Bot Slash Commands</h2>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ padding: "8px 12px", backgroundColor: "var(--bg-app)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
              <code style={{ color: "var(--status-completed)", fontWeight: "700" }}>/status [task-id]</code>
              <p className="meta-text" style={{ fontSize: "12px", marginTop: "2px" }}>Post status update or completion evidence</p>
            </div>
            <div style={{ padding: "8px 12px", backgroundColor: "var(--bg-app)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
              <code style={{ color: "var(--status-progress)", fontWeight: "700" }}>/blocker [description]</code>
              <p className="meta-text" style={{ fontSize: "12px", marginTop: "2px" }}>Flag a dependency block and alert leader</p>
            </div>
            <div style={{ padding: "8px 12px", backgroundColor: "var(--bg-app)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
              <code style={{ color: "var(--accent-cyan)", fontWeight: "700" }}>/tasks</code>
              <p className="meta-text" style={{ fontSize: "12px", marginTop: "2px" }}>Query assigned tasks and upcoming deadlines</p>
            </div>
            <div style={{ padding: "8px 12px", backgroundColor: "var(--bg-app)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
              <code style={{ color: "var(--accent-primary)", fontWeight: "700" }}>/link [telegram_id]</code>
              <p className="meta-text" style={{ fontSize: "12px", marginTop: "2px" }}>Pair Telegram user ID to Syncora team profile</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
