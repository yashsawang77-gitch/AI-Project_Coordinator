import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  MessageSquare,
  X,
  Send,
  Trash2,
  RefreshCw,
  Bot,
  User,
  AlertCircle,
  CheckCircle2,
  Minimize2,
  Maximize2,
  HelpCircle,
} from "lucide-react";
import { syncoraApi } from "../services/api";

const SUGGESTED_QUESTIONS = [
  "What tasks are assigned to me?",
  "Which tasks are overdue?",
  "What blockers need attention?",
  "Summarize my progress.",
  "How is my team workload distributed?",
  "What should I prioritize next?",
];

export function AIChatbox({ currentUser, onTaskStatusUpdated }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: "msg-welcome",
      role: "assistant",
      content:
        "👋 Hi! I am **Syncora AI**, your team project coordinator. Every answer I provide is grounded in live records from your task ledger, deadlines, and workload telemetry. What would you like to review?",
      timestamp: "Just now",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorState, setErrorState] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
    }
  }, [messages, isOpen, isMinimized, loading]);

  // Load chat history from backend on open
  useEffect(() => {
    if (isOpen && currentUser?.id) {
      syncoraApi
        .getAIChatHistory(currentUser.id)
        .then((history) => {
          if (history && history.length > 0) {
            setMessages(
              history.map((h) => ({
                id: h.id,
                role: h.role,
                content: h.content,
                timestamp: new Date(h.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                }),
              }))
            );
          }
        })
        .catch((e) => console.warn("Could not load chat history:", e));
    }
  }, [isOpen, currentUser?.id]);

  // Send message handler
  const handleSendMessage = async (textToSend = null) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || loading) return;

    setErrorState(null);
    setInputMessage("");

    const userMessageId = `user-${Date.now()}`;
    const userMsgObj = {
      id: userMessageId,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsgObj]);
    setLoading(true);

    try {
      const res = await syncoraApi.sendAIChat(currentUser?.id || "mem-1", text);
      setLoading(false);

      const aiMsgObj = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: res.reply,
        timestamp: res.timestamp || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        blockerAlert: res.blockerAlert,
        updatedTask: res.updatedTask,
      };

      setMessages((prev) => [...prev, aiMsgObj]);

      // If backend updated a task, notify parent to refresh lists
      if (res.updatedTask && onTaskStatusUpdated) {
        onTaskStatusUpdated(res.updatedTask);
      }
    } catch (err) {
      setLoading(false);
      setErrorState({
        failedText: text,
        message: err.message || "Failed to reach AI Coordinator. Please retry.",
      });
    }
  };

  // Clear chat conversation
  const handleClearChat = async () => {
    if (!window.confirm("Clear this conversation history?")) return;
    try {
      await syncoraApi.clearAIChatHistory(currentUser?.id || "mem-1");
      setMessages([
        {
          id: `msg-welcome-${Date.now()}`,
          role: "assistant",
          content: "Conversation cleared. Ready for your questions!",
          timestamp: "Just now",
        },
      ]);
    } catch (e) {
      console.warn("Could not clear history:", e);
    }
  };

  return (
    <>
      {/* ---------------- FLOATING ACTION BUTTON ---------------- */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => {
            setIsOpen(true);
            setIsMinimized(false);
          }}
          style={{
            position: "fixed",
            bottom: "28px",
            right: "28px",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "14px 22px",
            borderRadius: "999px",
            backgroundColor: "var(--accent-primary)",
            color: "#090d16",
            border: "none",
            boxShadow: "0 8px 30px rgba(24, 229, 180, 0.4)",
            fontWeight: "800",
            fontSize: "14px",
            cursor: "pointer",
            transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = "translateY(-3px) scale(1.03)")}
          onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0) scale(1)")}
        >
          <Sparkles size={18} />
          <span>Ask Syncora AI</span>
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: "#090d16",
              boxShadow: "0 0 8px #090d16",
            }}
          />
        </button>
      )}

      {/* ---------------- RESPONSIVE CHAT PANEL ---------------- */}
      {isOpen && (
        <div
          style={{
            position: "fixed",
            bottom: "28px",
            right: "28px",
            zIndex: 10000,
            width: "420px",
            maxWidth: "calc(100vw - 32px)",
            height: isMinimized ? "64px" : "600px",
            maxHeight: "calc(100vh - 48px)",
            display: "flex",
            flexDirection: "column",
            borderRadius: "18px",
            backgroundColor: "rgba(13, 20, 36, 0.96)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(24, 229, 180, 0.25)",
            boxShadow: "0 24px 60px rgba(0, 0, 0, 0.6), 0 0 25px rgba(24, 229, 180, 0.15)",
            overflow: "hidden",
            transition: "height 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        >
          {/* Top Chat Header */}
          <div
            style={{
              padding: "14px 18px",
              borderBottom: "1px solid var(--border-subtle)",
              backgroundColor: "rgba(8, 13, 25, 0.75)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "10px",
                  backgroundColor: "rgba(24, 229, 180, 0.15)",
                  border: "1px solid rgba(24, 229, 180, 0.3)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--accent-primary)",
                }}
              >
                <Bot size={20} />
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ fontSize: "14px", fontWeight: "800", color: "var(--text-white)" }}>
                    Syncora Assistant
                  </span>
                  <span
                    style={{
                      width: "7px",
                      height: "7px",
                      borderRadius: "50%",
                      backgroundColor: "var(--accent-primary)",
                      boxShadow: "0 0 8px var(--accent-primary)",
                    }}
                  />
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "1px" }}>
                  Grounded in SQLite Live Database
                </div>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              {!isMinimized && (
                <button
                  type="button"
                  onClick={handleClearChat}
                  title="Clear conversation"
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--text-muted)",
                    padding: "6px",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  <Trash2 size={15} />
                </button>
              )}

              <button
                type="button"
                onClick={() => setIsMinimized(!isMinimized)}
                title={isMinimized ? "Expand" : "Minimize"}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  padding: "6px",
                  borderRadius: "6px",
                  cursor: "pointer",
                }}
              >
                {isMinimized ? <Maximize2 size={15} /> : <Minimize2 size={15} />}
              </button>

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Close assistant"
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  padding: "6px",
                  borderRadius: "6px",
                  cursor: "pointer",
                }}
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Chat Messages Body */}
          {!isMinimized && (
            <>
              <div
                style={{
                  flex: 1,
                  overflowY: "auto",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "14px",
                }}
              >
                {messages.map((msg) => {
                  const isUser = msg.role === "user";
                  return (
                    <div
                      key={msg.id}
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: isUser ? "flex-end" : "flex-start",
                        gap: "4px",
                      }}
                    >
                      <div
                        style={{
                          maxWidth: "85%",
                          padding: "12px 14px",
                          borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                          backgroundColor: isUser ? "var(--accent-primary)" : "var(--bg-app)",
                          color: isUser ? "#090d16" : "var(--text-white)",
                          border: isUser ? "none" : "1px solid var(--border-subtle)",
                          fontSize: "13px",
                          lineHeight: "1.5",
                          whiteSpace: "pre-wrap",
                          boxShadow: isUser
                            ? "0 4px 14px rgba(24, 229, 180, 0.2)"
                            : "0 4px 12px rgba(0, 0, 0, 0.2)",
                        }}
                      >
                        {msg.content}
                      </div>
                      <span style={{ fontSize: "10px", color: "var(--text-muted)", padding: "0 4px" }}>
                        {msg.timestamp}
                      </span>
                    </div>
                  );
                })}

                {/* Loading state indicator */}
                {loading && (
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 4px" }}>
                    <div
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "8px",
                        backgroundColor: "rgba(24, 229, 180, 0.15)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "var(--accent-primary)",
                      }}
                    >
                      <Sparkles size={14} />
                    </div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        padding: "8px 14px",
                        borderRadius: "14px",
                        backgroundColor: "var(--bg-app)",
                        border: "1px solid var(--border-subtle)",
                      }}
                    >
                      <span className="dot-pulse" style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "var(--accent-primary)" }} />
                      <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>Consulting project records...</span>
                    </div>
                  </div>
                )}

                {/* Error State with Retry */}
                {errorState && (
                  <div
                    style={{
                      padding: "10px 14px",
                      borderRadius: "10px",
                      backgroundColor: "rgba(244, 63, 94, 0.1)",
                      border: "1px solid rgba(244, 63, 94, 0.3)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "8px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "#f43f5e" }}>
                      <AlertCircle size={15} />
                      <span>{errorState.message}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleSendMessage(errorState.failedText)}
                      style={{
                        background: "none",
                        border: "1px solid rgba(244, 63, 94, 0.4)",
                        borderRadius: "6px",
                        color: "#f43f5e",
                        padding: "4px 8px",
                        fontSize: "11px",
                        fontWeight: "700",
                        cursor: "pointer",
                      }}
                    >
                      Retry
                    </button>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Suggested Question Chips */}
              <div
                style={{
                  padding: "8px 14px",
                  borderTop: "1px solid rgba(255, 255, 255, 0.05)",
                  backgroundColor: "rgba(8, 13, 25, 0.4)",
                  overflowX: "auto",
                  whiteSpace: "nowrap",
                  display: "flex",
                  gap: "6px",
                }}
              >
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(q)}
                    disabled={loading}
                    style={{
                      padding: "5px 10px",
                      borderRadius: "999px",
                      backgroundColor: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      color: "var(--text-white)",
                      fontSize: "11px",
                      fontWeight: "600",
                      cursor: "pointer",
                      flexShrink: 0,
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(24, 229, 180, 0.15)")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.05)")}
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Message Input Bar */}
              <div
                style={{
                  padding: "12px 14px",
                  borderTop: "1px solid var(--border-subtle)",
                  backgroundColor: "var(--bg-app)",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Ask a question or report progress..."
                  disabled={loading}
                  style={{
                    flex: 1,
                    padding: "10px 14px",
                    borderRadius: "10px",
                    backgroundColor: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid var(--border-subtle)",
                    color: "var(--text-white)",
                    fontSize: "13px",
                    outline: "none",
                  }}
                />
                <button
                  type="button"
                  onClick={() => handleSendMessage()}
                  disabled={loading || !inputMessage.trim()}
                  className="btn-primary"
                  style={{
                    width: "38px",
                    height: "38px",
                    padding: "0",
                    borderRadius: "10px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    opacity: !inputMessage.trim() ? 0.5 : 1,
                  }}
                >
                  <Send size={16} />
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
