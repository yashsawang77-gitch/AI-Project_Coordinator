import React, { useState } from "react";
import {
  Eye,
  EyeOff,
  Sparkles,
  Lock,
  Mail,
  User,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  KeyRound,
  ShieldCheck,
  UserPlus,
  LogIn,
} from "lucide-react";
import { syncoraApi } from "../services/api";

export function LoginPage({ onLoginSuccess }) {
  // Views: "signin" | "register" | "forgot"
  const [view, setView] = useState("signin");

  // Sign In State
  const [email, setEmail] = useState("maya.chen@novastudio.ai");
  const [password, setPassword] = useState("password123");
  const [showPassword, setShowPassword] = useState(false);

  // Register State
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regRole, setRegRole] = useState("Team Member");
  const [showRegPassword, setShowRegPassword] = useState(false);

  // Forgot Password State
  const [forgotEmail, setForgotEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [forgotStep, setForgotStep] = useState(1); // 1: request token, 2: set new password

  // Feedback State
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Handle Sign In
  const handleSignIn = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (!email.trim() || !password) {
      setErrorMessage("Please enter both your email/username and password.");
      return;
    }

    setLoading(true);
    try {
      const res = await syncoraApi.login(email.trim(), password);
      setLoading(false);
      if (res && res.user) {
        onLoginSuccess(res.user, res.user.role);
      }
    } catch (err) {
      setLoading(false);
      setErrorMessage(err.message || "Failed to sign in. Please verify your credentials.");
    }
  };

  // Handle Quick Demo Preset Sign In
  const handleDemoLogin = async (presetRole) => {
    setErrorMessage("");
    setSuccessMessage("");
    setLoading(true);

    const demoEmail = presetRole === "leader" ? "maya.chen@novastudio.ai" : "alex.m@novastudio.ai";
    setEmail(demoEmail);
    setPassword("password123");

    try {
      const res = await syncoraApi.login(demoEmail, "password123", presetRole);
      setLoading(false);
      if (res && res.user) {
        onLoginSuccess(res.user, presetRole);
      }
    } catch (err) {
      setLoading(false);
      setErrorMessage(err.message || "Could not log into demo profile.");
    }
  };

  // Handle Registration
  const handleRegister = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (!regName.trim() || !regEmail.trim() || !regPassword) {
      setErrorMessage("Please fill in your name, email, and password.");
      return;
    }

    if (regPassword.length < 6) {
      setErrorMessage("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      const res = await syncoraApi.register({
        name: regName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        role: regRole,
      });
      setLoading(false);
      if (res && res.user) {
        onLoginSuccess(res.user, res.user.role);
      }
    } catch (err) {
      setLoading(false);
      setErrorMessage(err.message || "Registration failed. Please try a different email.");
    }
  };

  // Handle Forgot Password - Step 1: Request Token
  const handleRequestResetToken = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (!forgotEmail.trim()) {
      setErrorMessage("Please enter your registered email address.");
      return;
    }

    setLoading(true);
    try {
      const res = await syncoraApi.forgotPassword(forgotEmail.trim());
      setLoading(false);
      if (res.resetToken) {
        setResetToken(res.resetToken);
      }
      setSuccessMessage(res.message || "Reset token generated. Enter it below with your new password.");
      setForgotStep(2);
    } catch (err) {
      setLoading(false);
      setErrorMessage(err.message || "Failed to generate password reset token.");
    }
  };

  // Handle Forgot Password - Step 2: Set New Password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (!resetToken.trim() || !newPassword) {
      setErrorMessage("Please enter the reset token and your new password.");
      return;
    }

    if (newPassword.length < 6) {
      setErrorMessage("New password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      const res = await syncoraApi.resetPassword({
        email: forgotEmail.trim(),
        resetToken: resetToken.trim(),
        newPassword,
      });
      setLoading(false);
      setSuccessMessage(res.message || "Password updated successfully. You can now sign in.");
      setEmail(forgotEmail.trim());
      setPassword(newPassword);
      setTimeout(() => {
        setView("signin");
        setForgotStep(1);
      }, 1500);
    } catch (err) {
      setLoading(false);
      setErrorMessage(err.message || "Failed to reset password. Please check your token.");
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "24px",
        backgroundColor: "var(--bg-app)",
        background: "radial-gradient(ellipse at 50% 20%, rgba(99, 102, 241, 0.12) 0%, rgba(8, 13, 25, 0.98) 75%)",
      }}
    >
      {/* Brand Header */}
      <div style={{ textAlign: "center", marginBottom: "28px" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "10px",
            padding: "8px 16px",
            borderRadius: "999px",
            backgroundColor: "rgba(24, 229, 180, 0.08)",
            border: "1px solid rgba(24, 229, 180, 0.25)",
            marginBottom: "16px",
          }}
        >
          <Sparkles size={16} color="var(--accent-primary)" />
          <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--accent-primary)", letterSpacing: "0.5px" }}>
            SYNCORA AI · HACKATHON PLATFORM
          </span>
        </div>
        <h1 style={{ fontSize: "32px", fontWeight: "900", color: "var(--text-white)", letterSpacing: "-0.5px" }}>
          Syncora AI
        </h1>
        <p style={{ fontSize: "14px", color: "var(--text-muted)", marginTop: "6px" }}>
          Every Task Connected. Every Blocker Detected.
        </p>
      </div>

      {/* Main Card */}
      <div
        className="card"
        style={{
          width: "100%",
          maxWidth: "440px",
          backgroundColor: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "16px",
          padding: "32px",
          boxShadow: "0 20px 40px -15px rgba(0, 0, 0, 0.5)",
        }}
      >
        {/* Error / Success Alerts */}
        {errorMessage && (
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "10px",
              backgroundColor: "rgba(244, 63, 94, 0.1)",
              border: "1px solid rgba(244, 63, 94, 0.3)",
              color: "#f43f5e",
              fontSize: "13px",
              marginBottom: "20px",
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: "1px" }} />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "10px",
              backgroundColor: "rgba(24, 229, 180, 0.1)",
              border: "1px solid rgba(24, 229, 180, 0.3)",
              color: "var(--accent-primary)",
              fontSize: "13px",
              marginBottom: "20px",
            }}
          >
            <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: "1px" }} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* ---------------- VIEW 1: SIGN IN ---------------- */}
        {view === "signin" && (
          <>
            <div style={{ marginBottom: "22px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: "800", color: "var(--text-white)" }}>Sign In</h2>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
                Enter your credentials to access your task dashboard.
              </p>
            </div>

            <form onSubmit={handleSignIn} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                  USERNAME OR EMAIL
                </label>
                <div style={{ position: "relative" }}>
                  <Mail size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "14px" }} />
                  <input
                    type="text"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="maya.chen@novastudio.ai"
                    required
                    style={{
                      width: "100%",
                      padding: "12px 14px 12px 40px",
                      borderRadius: "10px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-white)",
                      fontSize: "14px",
                      outline: "none",
                    }}
                  />
                </div>
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <label style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-muted)" }}>
                    PASSWORD
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setView("forgot");
                      setForgotEmail(email);
                      setErrorMessage("");
                      setSuccessMessage("");
                    }}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--accent-primary)",
                      fontSize: "12px",
                      fontWeight: "600",
                      cursor: "pointer",
                      padding: "0",
                    }}
                  >
                    Forgot Password?
                  </button>
                </div>
                <div style={{ position: "relative" }}>
                  <Lock size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "14px" }} />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    style={{
                      width: "100%",
                      padding: "12px 42px 12px 40px",
                      borderRadius: "10px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-white)",
                      fontSize: "14px",
                      outline: "none",
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: "absolute",
                      right: "12px",
                      top: "12px",
                      background: "none",
                      border: "none",
                      color: "var(--text-muted)",
                      cursor: "pointer",
                      padding: "2px",
                    }}
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
                style={{
                  width: "100%",
                  padding: "12px",
                  fontSize: "14px",
                  fontWeight: "700",
                  marginTop: "6px",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                {loading ? "Signing in..." : <><LogIn size={16} /> Sign In</>}
              </button>
            </form>

            {/* Create Account Link */}
            <div style={{ textAlign: "center", marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                Don't have an account?{" "}
              </span>
              <button
                type="button"
                onClick={() => {
                  setView("register");
                  setErrorMessage("");
                  setSuccessMessage("");
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent-primary)",
                  fontSize: "13px",
                  fontWeight: "700",
                  cursor: "pointer",
                  padding: "0",
                }}
              >
                Create Account
              </button>
            </div>

            {/* Quick 1-Click Demo Login for Hackathon Judges */}
            <div
              style={{
                marginTop: "20px",
                padding: "14px",
                borderRadius: "12px",
                backgroundColor: "rgba(99, 102, 241, 0.06)",
                border: "1px dashed rgba(99, 102, 241, 0.3)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "10px" }}>
                <ShieldCheck size={14} color="#818cf8" />
                <span style={{ fontSize: "11px", fontWeight: "800", color: "#818cf8", letterSpacing: "0.5px" }}>
                  QUICK HACKATHON DEMO ACCESS
                </span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => handleDemoLogin("leader")}
                  disabled={loading}
                  style={{
                    padding: "8px 10px",
                    borderRadius: "8px",
                    backgroundColor: "rgba(139, 92, 246, 0.15)",
                    border: "1px solid rgba(139, 92, 246, 0.35)",
                    color: "#a78bfa",
                    fontSize: "12px",
                    fontWeight: "700",
                    cursor: "pointer",
                    textAlign: "center",
                  }}
                >
                  👑 Team Leader<br />
                  <span style={{ fontSize: "10px", fontWeight: "400", opacity: 0.8 }}>Maya Chen</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDemoLogin("member")}
                  disabled={loading}
                  style={{
                    padding: "8px 10px",
                    borderRadius: "8px",
                    backgroundColor: "rgba(6, 182, 212, 0.15)",
                    border: "1px solid rgba(6, 182, 212, 0.35)",
                    color: "#22d3ee",
                    fontSize: "12px",
                    fontWeight: "700",
                    cursor: "pointer",
                    textAlign: "center",
                  }}
                >
                  👤 Team Member<br />
                  <span style={{ fontSize: "10px", fontWeight: "400", opacity: 0.8 }}>Alex Morgan</span>
                </button>
              </div>
            </div>
          </>
        )}

        {/* ---------------- VIEW 2: REGISTRATION ---------------- */}
        {view === "register" && (
          <>
            <div style={{ marginBottom: "22px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: "800", color: "var(--text-white)" }}>Create Account</h2>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
                Join Syncora AI to coordinate tasks with your team.
              </p>
            </div>

            <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                  FULL NAME
                </label>
                <div style={{ position: "relative" }}>
                  <User size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "14px" }} />
                  <input
                    type="text"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    placeholder="e.g. Jordan Lee"
                    required
                    style={{
                      width: "100%",
                      padding: "12px 14px 12px 40px",
                      borderRadius: "10px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-white)",
                      fontSize: "14px",
                      outline: "none",
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                  EMAIL ADDRESS
                </label>
                <div style={{ position: "relative" }}>
                  <Mail size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "14px" }} />
                  <input
                    type="email"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="jordan.lee@novastudio.ai"
                    required
                    style={{
                      width: "100%",
                      padding: "12px 14px 12px 40px",
                      borderRadius: "10px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-white)",
                      fontSize: "14px",
                      outline: "none",
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                  PASSWORD (MIN 6 CHARACTERS)
                </label>
                <div style={{ position: "relative" }}>
                  <Lock size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "14px" }} />
                  <input
                    type={showRegPassword ? "text" : "password"}
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    placeholder="Choose a secure password"
                    required
                    minLength={6}
                    style={{
                      width: "100%",
                      padding: "12px 42px 12px 40px",
                      borderRadius: "10px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-white)",
                      fontSize: "14px",
                      outline: "none",
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowRegPassword(!showRegPassword)}
                    style={{
                      position: "absolute",
                      right: "12px",
                      top: "12px",
                      background: "none",
                      border: "none",
                      color: "var(--text-muted)",
                      cursor: "pointer",
                      padding: "2px",
                    }}
                  >
                    {showRegPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                  PROJECT ROLE
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <button
                    type="button"
                    onClick={() => setRegRole("Team Member")}
                    style={{
                      padding: "10px",
                      borderRadius: "10px",
                      backgroundColor: regRole === "Team Member" ? "var(--accent-primary-bg)" : "var(--bg-app)",
                      border: `1px solid ${regRole === "Team Member" ? "var(--accent-primary)" : "var(--border-subtle)"}`,
                      color: regRole === "Team Member" ? "var(--accent-primary)" : "var(--text-muted)",
                      fontSize: "13px",
                      fontWeight: "700",
                      cursor: "pointer",
                    }}
                  >
                    👤 Team Member
                  </button>
                  <button
                    type="button"
                    onClick={() => setRegRole("Team Leader")}
                    style={{
                      padding: "10px",
                      borderRadius: "10px",
                      backgroundColor: regRole === "Team Leader" ? "var(--accent-primary-bg)" : "var(--bg-app)",
                      border: `1px solid ${regRole === "Team Leader" ? "var(--accent-primary)" : "var(--border-subtle)"}`,
                      color: regRole === "Team Leader" ? "var(--accent-primary)" : "var(--text-muted)",
                      fontSize: "13px",
                      fontWeight: "700",
                      cursor: "pointer",
                    }}
                  >
                    👑 Team Leader
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
                style={{
                  width: "100%",
                  padding: "12px",
                  fontSize: "14px",
                  fontWeight: "700",
                  marginTop: "6px",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                {loading ? "Creating Account..." : <><UserPlus size={16} /> Register & Continue</>}
              </button>
            </form>

            <div style={{ textAlign: "center", marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                Already have an account?{" "}
              </span>
              <button
                type="button"
                onClick={() => {
                  setView("signin");
                  setErrorMessage("");
                  setSuccessMessage("");
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent-primary)",
                  fontSize: "13px",
                  fontWeight: "700",
                  cursor: "pointer",
                  padding: "0",
                }}
              >
                Sign In
              </button>
            </div>
          </>
        )}

        {/* ---------------- VIEW 3: FORGOT PASSWORD ---------------- */}
        {view === "forgot" && (
          <>
            <div style={{ marginBottom: "22px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: "800", color: "var(--text-white)" }}>Reset Password</h2>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
                {forgotStep === 1
                  ? "Enter your account email to receive a password reset token."
                  : "Enter the reset token and choose your new password."}
              </p>
            </div>

            {forgotStep === 1 ? (
              <form onSubmit={handleRequestResetToken} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                    REGISTERED EMAIL
                  </label>
                  <div style={{ position: "relative" }}>
                    <Mail size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "14px" }} />
                    <input
                      type="email"
                      value={forgotEmail}
                      onChange={(e) => setForgotEmail(e.target.value)}
                      placeholder="Enter your email"
                      required
                      style={{
                        width: "100%",
                        padding: "12px 14px 12px 40px",
                        borderRadius: "10px",
                        backgroundColor: "var(--bg-app)",
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-white)",
                        fontSize: "14px",
                        outline: "none",
                      }}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary"
                  style={{
                    width: "100%",
                    padding: "12px",
                    fontSize: "14px",
                    fontWeight: "700",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  {loading ? "Generating Token..." : <><KeyRound size={16} /> Send Reset Token</>}
                </button>
              </form>
            ) : (
              <form onSubmit={handleResetPassword} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                    RESET TOKEN
                  </label>
                  <input
                    type="text"
                    value={resetToken}
                    onChange={(e) => setResetToken(e.target.value)}
                    placeholder="e.g. 3F8A2D"
                    required
                    style={{
                      width: "100%",
                      padding: "12px 14px",
                      borderRadius: "10px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--accent-primary)",
                      fontWeight: "700",
                      fontSize: "14px",
                      outline: "none",
                      letterSpacing: "1px",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                    NEW PASSWORD (MIN 6 CHARACTERS)
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    required
                    minLength={6}
                    style={{
                      width: "100%",
                      padding: "12px 14px",
                      borderRadius: "10px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-white)",
                      fontSize: "14px",
                      outline: "none",
                    }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary"
                  style={{
                    width: "100%",
                    padding: "12px",
                    fontSize: "14px",
                    fontWeight: "700",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  {loading ? "Updating..." : "Update Password & Sign In"}
                </button>
              </form>
            )}

            <div style={{ textAlign: "center", marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--border-subtle)" }}>
              <button
                type="button"
                onClick={() => {
                  setView("signin");
                  setErrorMessage("");
                  setSuccessMessage("");
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: "13px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                ← Back to Sign In
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
