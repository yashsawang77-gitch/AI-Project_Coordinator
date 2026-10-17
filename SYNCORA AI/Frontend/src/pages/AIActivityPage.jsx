import React, { useState } from "react";
import { Sparkles, Zap, Check, MessageSquare, Bot, AlertTriangle } from "lucide-react";

export function AIActivityPage({ metrics = {} }) {
  const safeMetrics = {
    followUpsSent: 34,
    repliesReceived: 28,
    blockersDetected: 7,
    statusChanges: 19,
    clarifications: 4,
    ...metrics,
  };

  const [currentStep, setCurrentStep] = useState(1);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationLogs, setSimulationLogs] = useState([]);

  const steps = [
    { num: 1, label: "Message received" },
    { num: 2, label: "AI analyzing" },
    { num: 3, label: "Evidence detected" },
    { num: 4, label: "Status updated" },
  ];

  const handleRunSimulation = () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setCurrentStep(1);
    setSimulationLogs(["Inbound Telegram message received from @alexmorgan_ux"]);

    setTimeout(() => {
      setCurrentStep(2);
      setSimulationLogs((prev) => [
        ...prev,
        "Semantic Analyzer: Parsed '60% done', 'Charts working', 'validating filters'",
      ]);
    }, 1200);

    setTimeout(() => {
      setCurrentStep(3);
      setSimulationLogs((prev) => [
        ...prev,
        "Entity Match: Associated with SYNC-201 (Implement dashboard analytics)",
      ]);
    }, 2400);

    setTimeout(() => {
      setCurrentStep(4);
      setSimulationLogs((prev) => [
        ...prev,
        "Database: Updated SYNC-201 progress to 60%. Next milestone ping scheduled.",
      ]);
      setIsSimulating(false);
    }, 3800);
  };

  return (
    <div>
      {/* Syncora Intelligence Hero Banner */}
      <div className="ai-hero-banner">
        <div className="ai-hero-text">
          <div className="section-label">SYNCORA INTELLIGENCE</div>
          <h2>Your team, continuously synchronized.</h2>
          <p>
            Syncora follows up, understands replies, detects risk, and keeps work moving.
          </p>
        </div>

        <div className="ai-glowing-orb">
          <Sparkles size={34} />
        </div>
      </div>

      {/* 5 AI Metrics Cards */}
      <div className="ai-stats-row">
        <div className="ai-stat-box">
          <span className="ai-stat-num">{safeMetrics.followUpsSent}</span>
          <span className="ai-stat-title">Follow-ups sent</span>
        </div>
        <div className="ai-stat-box">
          <span className="ai-stat-num">{safeMetrics.repliesReceived}</span>
          <span className="ai-stat-title">Replies received</span>
        </div>
        <div className="ai-stat-box">
          <span className="ai-stat-num" style={{ color: "var(--status-blocked)" }}>
            {safeMetrics.blockersDetected}
          </span>
          <span className="ai-stat-title">Blockers detected</span>
        </div>
        <div className="ai-stat-box">
          <span className="ai-stat-num" style={{ color: "var(--status-completed)" }}>
            {safeMetrics.statusChanges}
          </span>
          <span className="ai-stat-title">Status changes</span>
        </div>
        <div className="ai-stat-box">
          <span className="ai-stat-num" style={{ color: "var(--accent-primary)" }}>
            {safeMetrics.clarifications}
          </span>
          <span className="ai-stat-title">Clarifications</span>
        </div>
      </div>

      {/* Interactive Demo Card */}
      <div className="interactive-demo-card">
        <div className="demo-header-row">
          <div>
            <div className="section-label">INTERACTIVE DEMO</div>
            <h2 className="section-title">AI reply workflow</h2>
          </div>

          <button
            type="button"
            className="btn-primary"
            onClick={handleRunSimulation}
            disabled={isSimulating}
          >
            <Zap size={16} />
            {isSimulating ? "Running simulation..." : "Run simulation"}
          </button>
        </div>

        {/* 4-Step Pipeline Stepper */}
        <div className="workflow-stepper">
          {steps.map((step, idx) => {
            const isCompleted = step.num < currentStep;
            const isActive = step.num === currentStep;

            return (
              <React.Fragment key={step.num}>
                <div className="step-node">
                  <div
                    className={`step-circle ${
                      isCompleted ? "completed" : isActive ? "active" : ""
                    }`}
                  >
                    {isCompleted ? <Check size={16} /> : step.num}
                  </div>
                  <span className="step-label">{step.label}</span>
                </div>

                {idx < steps.length - 1 && (
                  <div
                    className={`step-line ${
                      step.num < currentStep ? "active" : ""
                    }`}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Message Preview Box */}
        <div className="telegram-message-preview">
          <div className="tg-avatar">AM</div>
          <div className="tg-content">
            <div className="tg-sender-info">
              <span>Alex Morgan</span>
              <span className="tg-tag">Telegram</span>
            </div>
            <p className="tg-bubble-text">
              "The analytics module is around 60% done. Charts are working; I'm validating the filters now."
            </p>
            <span className="tg-time">Received 2 minutes ago</span>
          </div>
        </div>

        {/* Live Simulation Output Feed */}
        {simulationLogs.length > 0 && (
          <div
            style={{
              marginTop: "20px",
              padding: "16px",
              backgroundColor: "var(--bg-app)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "10px",
              fontFamily: "monospace",
              fontSize: "13px",
              color: "var(--accent-primary)",
            }}
          >
            <div style={{ color: "var(--status-completed)", fontWeight: "700", marginBottom: "8px" }}>
              AI Pipeline Execution Logs:
            </div>
            {simulationLogs.map((log, index) => (
              <div key={index} style={{ marginBottom: "4px" }}>
                <span style={{ color: "var(--text-muted)" }}>[{new Date().toLocaleTimeString()}]</span> {log}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

