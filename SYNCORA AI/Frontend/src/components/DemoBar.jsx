import React, { useState } from "react";
import {
  Sparkles,
  RotateCcw,
  CheckCircle2,
  ChevronRight,
  ShieldCheck,
  X,
  ExternalLink,
  BookOpen,
} from "lucide-react";
import { syncoraApi } from "../services/api";

const DEMO_STEPS = [
  { step: 1, title: "Sign in to Syncora AI", detail: "Use Maya Chen (Team Leader) or Alex Morgan (Member) with 1-click access." },
  { step: 2, title: "Open Team Leader Dashboard", detail: "View overview KPIs, task distribution donut chart, and team pulse capacity." },
  { step: 3, title: "Assign a Task to Demo Member", detail: "Click '+ Create Task' and assign work to Alex Morgan." },
  { step: 4, title: "Task Notification in Telegram", detail: "Alex receives real-time assignment alert with priority & deadline in Telegram." },
  { step: 5, title: "View Assigned Tasks in Telegram", detail: "Type /mytasks in Telegram bot to inspect assigned items and interactive buttons." },
  { step: 6, title: "Mark Task Complete from Telegram", detail: "Tap 'Complete' in Telegram to mark the task completed." },
  { step: 7, title: "Live Sync on Website", detail: "The website tasks list and sprint overview update immediately." },
  { step: 8, title: "Report a Blocker via Telegram", detail: "Type /blocker Waiting on credentials to flag an urgent roadblock." },
  { step: 9, title: "Blocker Alert on Website", detail: "Task is highlighted with red accent bar and leader notification appears." },
  { step: 10, title: "Open Website AI Chatbox", detail: "Click 'Ask Syncora AI' floating button in the bottom right corner." },
  { step: 11, title: "Ask: 'Which tasks are overdue?'", detail: "Assistant cites SYNC-198 directly from SQLite database." },
  { step: 12, title: "Demonstrate Grounded AI", detail: "Ask 'What should I prioritize next?' to view verified recommendations." },
];

export function DemoBar({ onResetSuccess }) {
  const [isResetting, setIsResetting] = useState(false);
  const [showWalkthrough, setShowWalkthrough] = useState(false);
  const [resetMessage, setResetMessage] = useState(null);

  const handleReset = async () => {
    if (!window.confirm("Reset all project records and demo accounts to clean hackathon starting state?")) return;
    setIsResetting(true);
    try {
      const res = await syncoraApi.resetDemoData();
      setIsResetting(false);
      setResetMessage("✓ Demo workspace reset to pristine starting state!");
      setTimeout(() => setResetMessage(null), 3000);
      if (onResetSuccess) {
        onResetSuccess();
      }
    } catch (e) {
      setIsResetting(false);
      alert("Failed to reset demo data: " + e.message);
    }
  };

  return (
    <>
      {/* Top Banner */}
      <div
        style={{
          backgroundColor: "rgba(99, 102, 241, 0.12)",
          borderBottom: "1px solid rgba(99, 102, 241, 0.25)",
          padding: "6px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "10px",
          fontSize: "12px",
          color: "var(--text-white)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            style={{
              padding: "2px 8px",
              borderRadius: "4px",
              backgroundColor: "rgba(99, 102, 241, 0.25)",
              color: "#a5b4fc",
              fontWeight: "800",
              fontSize: "10px",
              letterSpacing: "0.5px",
            }}
          >
            DEMO MODE
          </span>
          <span style={{ color: "var(--text-muted)" }}>
            College Hackathon Presentation · Nova Studio Workspace
          </span>
          {resetMessage && (
            <span style={{ color: "var(--accent-primary)", fontWeight: "700", marginLeft: "8px" }}>
              {resetMessage}
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button
            type="button"
            onClick={() => setShowWalkthrough(true)}
            style={{
              background: "none",
              border: "none",
              color: "#818cf8",
              fontWeight: "700",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "2px 6px",
            }}
          >
            <BookOpen size={13} /> Judge Walkthrough Guide (12 Steps)
          </button>

          <span style={{ color: "rgba(255, 255, 255, 0.2)" }}>|</span>

          <button
            type="button"
            onClick={handleReset}
            disabled={isResetting}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted)",
              fontWeight: "600",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "2px 6px",
            }}
            title="Reset database to clean starting seed"
          >
            <RotateCcw size={12} className={isResetting ? "spin" : ""} />
            {isResetting ? "Resetting..." : "Reset Demo Data"}
          </button>
        </div>
      </div>

      {/* Walkthrough Modal */}
      {showWalkthrough && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 20000,
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            className="card"
            style={{
              width: "100%",
              maxWidth: "680px",
              maxHeight: "85vh",
              overflowY: "auto",
              padding: "28px",
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "16px",
              boxShadow: "0 25px 60px rgba(0, 0, 0, 0.7)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px" }}>
              <div>
                <div className="section-label">HACKATHON DEMO PRESENTATION</div>
                <h2 style={{ fontSize: "20px", fontWeight: "900", color: "var(--text-white)", marginTop: "2px" }}>
                  12-Step Live Demonstration Walkthrough
                </h2>
                <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
                  Follow this structured sequence to demonstrate the entire platform to judges.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowWalkthrough(false)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  padding: "6px",
                  cursor: "pointer",
                }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {DEMO_STEPS.map((s) => (
                <div
                  key={s.step}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "12px",
                    padding: "10px 14px",
                    borderRadius: "10px",
                    backgroundColor: "var(--bg-app)",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  <div
                    style={{
                      width: "24px",
                      height: "24px",
                      borderRadius: "50%",
                      backgroundColor: "rgba(24, 229, 180, 0.15)",
                      color: "var(--accent-primary)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "11px",
                      fontWeight: "800",
                      flexShrink: 0,
                      marginTop: "2px",
                    }}
                  >
                    {s.step}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-white)" }}>
                      {s.title}
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                      {s.detail}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--border-subtle)" }}>
              <button
                type="button"
                onClick={() => setShowWalkthrough(false)}
                className="btn-primary"
                style={{ padding: "8px 18px", fontSize: "13px" }}
              >
                Got It, Start Demo
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
