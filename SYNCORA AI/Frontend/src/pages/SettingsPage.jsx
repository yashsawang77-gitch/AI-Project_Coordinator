import React, { useState, useEffect } from "react";
import {
  Save,
  Server,
  Shield,
  LogOut,
  Phone,
  CheckCircle2,
  AlertCircle,
  Clock,
  Send,
  RefreshCw,
  ExternalLink,
  Unlink,
  MessageSquare,
  Sparkles,
  Smartphone,
  Check,
  User,
  Briefcase,
  Zap,
} from "lucide-react";
import { syncoraApi } from "../services/api";

export function SettingsPage({ currentUser, onLogout, onUpdateUser }) {
  // Server / API Settings
  const [apiUrl, setApiUrl] = useState(
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api"
  );

  // Profile Details State
  const [name, setName] = useState(currentUser?.name || "Maya Chen");
  const [title, setTitle] = useState(currentUser?.title || "Team Leader");
  const [capacityHours, setCapacityHours] = useState(currentUser?.availableCapacityHours || 35);
  const [skills, setSkills] = useState(currentUser?.skills || "Architecture, Python, AI Coordination");
  const [profileSaved, setProfileSaved] = useState(false);

  // Phone Verification State (Phase 3)
  const [countryCode, setCountryCode] = useState("+91");
  const [phoneNumber, setPhoneNumber] = useState(currentUser?.phoneNumber || "");
  const [isPhoneVerified, setIsPhoneVerified] = useState(Boolean(currentUser?.isPhoneVerified));
  const [verifiedAt, setVerifiedAt] = useState(currentUser?.phoneVerifiedAt || null);
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpCountdown, setOtpCountdown] = useState(0);
  const [otpLoading, setOtpLoading] = useState(false);
  const [phoneMessage, setPhoneMessage] = useState(null); // { type: "success" | "error" | "info", text: string }
  const [providerInfo, setProviderInfo] = useState({ provider: "dev", configured: true });
  const [sandboxOtpDisclosed, setSandboxOtpDisclosed] = useState(null);

  // Telegram Integration State (Phase 4)
  const [telegramConnected, setTelegramConnected] = useState(Boolean(currentUser?.telegramConnected));
  const [telegramHandle, setTelegramHandle] = useState(currentUser?.telegramHandle || "");
  const [telegramUserId, setTelegramUserId] = useState(currentUser?.telegramUserId || "");
  const [telegramBotUsername, setTelegramBotUsername] = useState("@Syncoraaivalidbot");
  const [telegramLoading, setTelegramLoading] = useState(false);
  const [telegramDeepLink, setTelegramDeepLink] = useState(null);
  const [telegramMessage, setTelegramMessage] = useState(null);

  // Fetch live phone & telegram status from backend on mount
  useEffect(() => {
    async function fetchIntegrationStatus() {
      try {
        const phoneStatus = await syncoraApi.getPhoneStatus();
        if (phoneStatus) {
          setIsPhoneVerified(phoneStatus.isVerified);
          if (phoneStatus.phoneNumber) setPhoneNumber(phoneStatus.phoneNumber);
          if (phoneStatus.verifiedAt) setVerifiedAt(phoneStatus.verifiedAt);
          setProviderInfo({
            provider: phoneStatus.provider,
            configured: phoneStatus.providerConfigured,
          });
        }
      } catch (e) {
        console.warn("Could not fetch phone status:", e);
      }

      try {
        const me = await syncoraApi.getMe();
        if (me) {
          setIsPhoneVerified(Boolean(me.isPhoneVerified));
          setTelegramConnected(Boolean(me.telegramConnected));
          if (me.telegramHandle) setTelegramHandle(me.telegramHandle);
          if (me.telegramUserId) setTelegramUserId(me.telegramUserId);
          if (me.phoneNumber) setPhoneNumber(me.phoneNumber);
        }
      } catch (e) {
        // fallback
      }

      try {
        const tgStatus = await syncoraApi.getTelegramIntegrationStatus();
        if (tgStatus && tgStatus.botName) {
          setTelegramBotUsername(tgStatus.botName);
        }
      } catch (e) {
        // fallback
      }
    }
    fetchIntegrationStatus();
  }, []);

  // OTP Countdown Timer
  useEffect(() => {
    let timer;
    if (otpCountdown > 0) {
      timer = setInterval(() => {
        setOtpCountdown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [otpCountdown]);

  // Handle Save Profile Details
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      await syncoraApi.updateProfile({
        name,
        title,
        skills,
        availableCapacityHours: Number(capacityHours),
      });
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 2500);
      if (onUpdateUser) {
        onUpdateUser({
          ...currentUser,
          name,
          title,
          skills,
          availableCapacityHours: Number(capacityHours),
        });
      }
    } catch (err) {
      setProfileSaved(false);
    }
  };

  // Phase 3: Send OTP Handler
  const handleSendOtp = async (e) => {
    e?.preventDefault();
    setPhoneMessage(null);
    setSandboxOtpDisclosed(null);

    if (!phoneNumber.trim()) {
      setPhoneMessage({ type: "error", text: "Please enter your phone number." });
      return;
    }

    setOtpLoading(true);
    try {
      const res = await syncoraApi.sendPhoneOtp(phoneNumber.trim(), countryCode);
      setOtpLoading(false);
      setOtpSent(true);
      setOtpCountdown(60);
      setPhoneMessage({ type: "success", text: res.message });
      if (res.isDemoSandbox && res.sandboxOtp) {
        setSandboxOtpDisclosed(res.sandboxOtp);
      }
    } catch (err) {
      setOtpLoading(false);
      setPhoneMessage({
        type: "error",
        text: err.message || "Failed to send OTP. Please check credentials or phone format.",
      });
    }
  };

  // Phase 3: Verify OTP Handler
  const handleVerifyOtp = async (e) => {
    e?.preventDefault();
    setPhoneMessage(null);

    if (!otp.trim() || otp.trim().length !== 6) {
      setPhoneMessage({ type: "error", text: "Please enter the complete 6-digit verification code." });
      return;
    }

    setOtpLoading(true);
    try {
      const res = await syncoraApi.verifyPhoneOtp(phoneNumber.trim(), otp.trim());
      setOtpLoading(false);
      if (res.verified) {
        setIsPhoneVerified(true);
        setVerifiedAt(res.verifiedAt || new Date().toISOString());
        setOtpSent(false);
        setOtp("");
        setSandboxOtpDisclosed(null);
        setPhoneMessage({ type: "success", text: "✓ Phone number verified successfully!" });
      }
    } catch (err) {
      setOtpLoading(false);
      setPhoneMessage({
        type: "error",
        text: err.message || "Invalid or expired OTP. Please try again.",
      });
    }
  };

  // Phase 3: Change Number Handler
  const handleChangeNumber = async () => {
    if (!window.confirm("Changing your phone number will require re-verification. Continue?")) return;
    try {
      await syncoraApi.changePhoneNumber();
      setIsPhoneVerified(false);
      setVerifiedAt(null);
      setOtpSent(false);
      setOtp("");
      setSandboxOtpDisclosed(null);
      setPhoneMessage({ type: "info", text: "Phone number cleared. Enter your new number below." });
    } catch (e) {
      console.error("Change number error:", e);
    }
  };

  // Phase 4: Connect Telegram Handler
  const handleConnectTelegram = async () => {
    setTelegramMessage(null);
    setTelegramDeepLink(null);

    if (!isPhoneVerified) {
      setTelegramMessage({
        type: "error",
        text: "Phone verification required: Please verify your phone number above before connecting Telegram.",
      });
      return;
    }

    setTelegramLoading(true);
    try {
      const res = await syncoraApi.getTelegramLinkToken();
      setTelegramLoading(false);
      if (res && res.deepLink) {
        setTelegramDeepLink(res.deepLink);
        if (res.botUsername) {
          setTelegramBotUsername(res.botUsername);
        }
        // Open deep link in new tab or popup
        window.open(res.deepLink, "_blank", "noopener,noreferrer");
        setTelegramMessage({
          type: "success",
          text: "Deep link generated! Telegram is opening. Press 'Start' in the bot to complete account linking.",
        });
      }
    } catch (err) {
      setTelegramLoading(false);
      setTelegramMessage({
        type: "error",
        text: err.message || "Failed to generate Telegram connection link.",
      });
    }
  };

  // Phase 4: Disconnect Telegram Handler
  const handleDisconnectTelegram = async () => {
    if (!window.confirm("Disconnect your Telegram account from Syncora AI? You will stop receiving task updates.")) return;
    setTelegramLoading(true);
    try {
      await syncoraApi.disconnectTelegram();
      setTelegramLoading(false);
      setTelegramConnected(false);
      setTelegramHandle("");
      setTelegramUserId("");
      setTelegramDeepLink(null);
      setTelegramMessage({ type: "info", text: "Telegram account successfully disconnected." });
    } catch (err) {
      setTelegramLoading(false);
      setTelegramMessage({ type: "error", text: "Failed to disconnect Telegram." });
    }
  };

  // Refresh Connection Status
  const handleRefreshTelegramStatus = async () => {
    setTelegramLoading(true);
    try {
      const me = await syncoraApi.getMe();
      setTelegramLoading(false);
      if (me && me.telegramConnected) {
        setTelegramConnected(true);
        setTelegramHandle(me.telegramHandle || "");
        setTelegramUserId(me.telegramUserId || "");
        setTelegramDeepLink(null);
        setTelegramMessage({ type: "success", text: "✓ Telegram connection verified and active!" });
      } else {
        setTelegramMessage({ type: "info", text: "Still waiting for /start in Telegram. Please tap Start in the bot." });
      }
    } catch (e) {
      setTelegramLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "860px", paddingBottom: "40px" }}>
      {/* ---------------- 1. ACCOUNT PROFILE CARD ---------------- */}
      <div className="card">
        <div className="section-label">ACCOUNT PROFILE</div>
        <h2 className="section-title" style={{ marginBottom: "16px" }}>Active Session & Team Details</h2>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px", marginBottom: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <div
              style={{
                width: "52px",
                height: "52px",
                borderRadius: "14px",
                backgroundColor: currentUser?.role === "member" ? "var(--accent-cyan)" : "var(--accent-primary)",
                color: "#090d16",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: "900",
                fontSize: "18px",
              }}
            >
              {(name || "MC").split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "18px", fontWeight: "800", color: "var(--text-white)" }}>
                  {name}
                </span>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: "700",
                    padding: "2px 8px",
                    borderRadius: "6px",
                    backgroundColor: currentUser?.role === "member" ? "var(--accent-cyan-bg)" : "var(--accent-primary-bg)",
                    color: currentUser?.role === "member" ? "var(--accent-cyan)" : "var(--accent-primary)",
                  }}
                >
                  {currentUser?.role === "member" ? "👤 Team Member" : "👑 Team Leader"}
                </span>
              </div>
              <div style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "2px" }}>
                {currentUser?.email || "maya.chen@novastudio.ai"} · <span style={{ color: "var(--accent-primary)", fontWeight: "600" }}>{title}</span>
              </div>
            </div>
          </div>

          <button
            type="button"
            className="btn-secondary"
            onClick={onLogout}
            style={{ color: "var(--status-blocked)", borderColor: "var(--status-blocked-border)" }}
          >
            <LogOut size={16} /> Sign Out
          </button>
        </div>

        {/* Edit Profile Form (Moved from Login screen) */}
        <form onSubmit={handleSaveProfile} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "16px", paddingTop: "16px", borderTop: "1px solid var(--border-subtle)" }}>
          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "8px",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-white)",
                fontSize: "13px",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
              Job Title / Specialization
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "8px",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-white)",
                fontSize: "13px",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
              Weekly Capacity (Hours)
            </label>
            <input
              type="number"
              min={10}
              max={60}
              value={capacityHours}
              onChange={(e) => setCapacityHours(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "8px",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-white)",
                fontSize: "13px",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
              Key Skills / Specializations
            </label>
            <input
              type="text"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="e.g. React, Python, UI/UX"
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "8px",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-white)",
                fontSize: "13px",
              }}
            />
          </div>

          <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "10px", marginTop: "4px" }}>
            {profileSaved && (
              <span style={{ fontSize: "12px", color: "var(--accent-primary)", fontWeight: "700", display: "flex", alignItems: "center", gap: "4px" }}>
                <Check size={14} /> Profile Saved
              </span>
            )}
            <button type="submit" className="btn-primary" style={{ padding: "8px 16px", fontSize: "13px" }}>
              <Save size={14} /> Save Profile Changes
            </button>
          </div>
        </form>
      </div>

      {/* ---------------- 2. REAL PHONE NUMBER OTP VERIFICATION (PHASE 3) ---------------- */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div className="section-label">SECURITY & VERIFICATION</div>
            <h2 className="section-title" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Phone size={20} color="var(--accent-primary)" />
              Phone Number OTP Verification
            </h2>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
              Verify your phone number with a one-time SMS passcode to enable Telegram account linking.
            </p>
          </div>

          {/* Verification Status Badge */}
          <div>
            {isPhoneVerified ? (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 14px",
                  borderRadius: "999px",
                  backgroundColor: "rgba(24, 229, 180, 0.12)",
                  border: "1px solid rgba(24, 229, 180, 0.35)",
                  color: "var(--accent-primary)",
                  fontWeight: "800",
                  fontSize: "12px",
                }}
              >
                <CheckCircle2 size={16} /> Verified Phone
              </div>
            ) : (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 14px",
                  borderRadius: "999px",
                  backgroundColor: "rgba(245, 158, 11, 0.12)",
                  border: "1px solid rgba(245, 158, 11, 0.35)",
                  color: "#f59e0b",
                  fontWeight: "800",
                  fontSize: "12px",
                }}
              >
                <AlertCircle size={16} /> Unverified
              </div>
            )}
          </div>
        </div>

        {/* Feedback message banner */}
        {phoneMessage && (
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "10px",
              marginTop: "16px",
              fontSize: "13px",
              backgroundColor:
                phoneMessage.type === "error"
                  ? "rgba(244, 63, 94, 0.1)"
                  : phoneMessage.type === "success"
                  ? "rgba(24, 229, 180, 0.1)"
                  : "rgba(99, 102, 241, 0.1)",
              border: `1px solid ${
                phoneMessage.type === "error"
                  ? "rgba(244, 63, 94, 0.3)"
                  : phoneMessage.type === "success"
                  ? "rgba(24, 229, 180, 0.3)"
                  : "rgba(99, 102, 241, 0.3)"
              }`,
              color:
                phoneMessage.type === "error"
                  ? "#f43f5e"
                  : phoneMessage.type === "success"
                  ? "var(--accent-primary)"
                  : "#a5b4fc",
            }}
          >
            {phoneMessage.type === "error" ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
            <span>{phoneMessage.text}</span>
          </div>
        )}

        {/* Disclosed Sandbox OTP for Local Demo / Evaluation */}
        {sandboxOtpDisclosed && (
          <div
            style={{
              marginTop: "12px",
              padding: "12px 14px",
              borderRadius: "10px",
              backgroundColor: "rgba(99, 102, 241, 0.08)",
              border: "1px dashed rgba(99, 102, 241, 0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div style={{ fontSize: "12px", color: "#c7d2fe" }}>
              <strong>Sandbox Demo Mode OTP:</strong> <code style={{ fontSize: "14px", fontWeight: "800", color: "#818cf8", letterSpacing: "2px" }}>{sandboxOtpDisclosed}</code>
              <span style={{ display: "block", fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                (Live Twilio cellular SMS requires configuring TWILIO_ACCOUNT_SID in backend/.env)
              </span>
            </div>
            <button
              type="button"
              onClick={() => setOtp(sandboxOtpDisclosed)}
              style={{
                padding: "4px 10px",
                borderRadius: "6px",
                backgroundColor: "rgba(99, 102, 241, 0.2)",
                border: "1px solid rgba(99, 102, 241, 0.4)",
                color: "#c7d2fe",
                fontSize: "11px",
                fontWeight: "700",
                cursor: "pointer",
              }}
            >
              Auto-fill OTP
            </button>
          </div>
        )}

        {/* Verification Flow */}
        <div style={{ marginTop: "20px" }}>
          {isPhoneVerified ? (
            /* Verified state view */
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "14px",
                padding: "16px",
                borderRadius: "12px",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div>
                <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Verified Phone Number
                </div>
                <div style={{ fontSize: "16px", fontWeight: "800", color: "var(--text-white)", marginTop: "4px", letterSpacing: "0.5px" }}>
                  {phoneNumber}
                </div>
                {verifiedAt && (
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                    Verified on: {new Date(verifiedAt).toLocaleString()}
                  </div>
                )}
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleChangeNumber}
                style={{ fontSize: "12px", padding: "8px 14px" }}
              >
                Change Number
              </button>
            </div>
          ) : (
            /* Unverified input & OTP form */
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Phone input row */}
              <div style={{ display: "grid", gridTemplateColumns: "110px 1fr auto", gap: "10px", alignItems: "flex-end" }}>
                <div>
                  <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                    COUNTRY
                  </label>
                  <select
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    disabled={otpSent}
                    style={{
                      width: "100%",
                      padding: "11px 8px",
                      borderRadius: "8px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-white)",
                      fontSize: "13px",
                      fontWeight: "700",
                    }}
                  >
                    <option value="+91">🇮🇳 +91 (India)</option>
                    <option value="+1">🇺🇸 +1 (US)</option>
                    <option value="+44">🇬🇧 +44 (UK)</option>
                    <option value="+65">🇸🇬 +65 (SG)</option>
                    <option value="+61">🇦🇺 +61 (AU)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                    MOBILE PHONE NUMBER
                  </label>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="9876543210"
                    disabled={otpSent}
                    style={{
                      width: "100%",
                      padding: "11px 12px",
                      borderRadius: "8px",
                      backgroundColor: "var(--bg-app)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-white)",
                      fontSize: "14px",
                      letterSpacing: "0.5px",
                    }}
                  />
                </div>

                <div>
                  <button
                    type="button"
                    onClick={handleSendOtp}
                    disabled={otpLoading || (otpSent && otpCountdown > 0)}
                    className="btn-primary"
                    style={{
                      padding: "11px 18px",
                      fontSize: "13px",
                      fontWeight: "700",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {otpLoading ? (
                      "Sending..."
                    ) : otpSent && otpCountdown > 0 ? (
                      `Resend in ${otpCountdown}s`
                    ) : otpSent ? (
                      <><RefreshCw size={14} /> Resend OTP</>
                    ) : (
                      <><Send size={14} /> Send OTP</>
                    )}
                  </button>
                </div>
              </div>

              {/* OTP Input & Verification Row (appears once OTP is requested) */}
              {otpSent && (
                <div
                  style={{
                    padding: "16px",
                    borderRadius: "12px",
                    backgroundColor: "rgba(24, 229, 180, 0.04)",
                    border: "1px solid rgba(24, 229, 180, 0.2)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "12px",
                  }}
                >
                  <div style={{ flex: 1, minWidth: "220px" }}>
                    <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
                      ENTER 6-DIGIT VERIFICATION CODE
                    </label>
                    <input
                      type="text"
                      maxLength={6}
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                      placeholder="123456"
                      autoFocus
                      style={{
                        width: "100%",
                        maxWidth: "200px",
                        padding: "10px 14px",
                        borderRadius: "8px",
                        backgroundColor: "var(--bg-app)",
                        border: "1px solid var(--accent-primary)",
                        color: "var(--text-white)",
                        fontSize: "16px",
                        fontWeight: "800",
                        letterSpacing: "4px",
                        textAlign: "center",
                      }}
                    />
                  </div>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      onClick={() => {
                        setOtpSent(false);
                        setOtp("");
                        setSandboxOtpDisclosed(null);
                      }}
                      className="btn-secondary"
                      style={{ padding: "10px 14px", fontSize: "13px" }}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleVerifyOtp}
                      disabled={otpLoading || otp.length !== 6}
                      className="btn-primary"
                      style={{ padding: "10px 20px", fontSize: "13px", fontWeight: "700" }}
                    >
                      {otpLoading ? "Verifying..." : "Verify OTP"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ---------------- 3. SECURE TELEGRAM ACCOUNT LINKING (PHASE 4) ---------------- */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div className="section-label">TELEGRAM INTEGRATION</div>
            <h2 className="section-title" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <MessageSquare size={20} color="var(--accent-cyan)" />
              Telegram Account Linking
            </h2>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
              Link your Telegram account to chat with the Syncora AI bot and receive instant task alerts.
            </p>
          </div>

          <div>
            {telegramConnected ? (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 14px",
                  borderRadius: "999px",
                  backgroundColor: "rgba(6, 182, 212, 0.12)",
                  border: "1px solid rgba(6, 182, 212, 0.35)",
                  color: "var(--accent-cyan)",
                  fontWeight: "800",
                  fontSize: "12px",
                }}
              >
                <CheckCircle2 size={16} /> Linked & Active
              </div>
            ) : (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 14px",
                  borderRadius: "999px",
                  backgroundColor: "rgba(100, 116, 139, 0.15)",
                  border: "1px solid rgba(100, 116, 139, 0.3)",
                  color: "var(--text-muted)",
                  fontWeight: "700",
                  fontSize: "12px",
                }}
              >
                Not Connected
              </div>
            )}
          </div>
        </div>

        {/* Telegram Messages Banner */}
        {telegramMessage && (
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "10px",
              marginTop: "16px",
              fontSize: "13px",
              backgroundColor:
                telegramMessage.type === "error"
                  ? "rgba(244, 63, 94, 0.1)"
                  : telegramMessage.type === "success"
                  ? "rgba(6, 182, 212, 0.1)"
                  : "rgba(99, 102, 241, 0.1)",
              border: `1px solid ${
                telegramMessage.type === "error"
                  ? "rgba(244, 63, 94, 0.3)"
                  : telegramMessage.type === "success"
                  ? "rgba(6, 182, 212, 0.3)"
                  : "rgba(99, 102, 241, 0.3)"
              }`,
              color:
                telegramMessage.type === "error"
                  ? "#f43f5e"
                  : telegramMessage.type === "success"
                  ? "var(--accent-cyan)"
                  : "#a5b4fc",
            }}
          >
            {telegramMessage.type === "error" ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
            <span>{telegramMessage.text}</span>
          </div>
        )}

        {/* Deep Link Ready Banner */}
        {telegramDeepLink && (
          <div
            style={{
              marginTop: "16px",
              padding: "16px",
              borderRadius: "12px",
              backgroundColor: "rgba(6, 182, 212, 0.08)",
              border: "1px solid rgba(6, 182, 212, 0.25)",
            }}
          >
            <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-white)", marginBottom: "6px" }}>
              🔗 1-Click Telegram Deep Link Ready
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "12px" }}>
              Click below to open Telegram directly. When prompted, tap <strong>Start</strong> to finalize account linking.
            </div>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              <a
                href={telegramDeepLink}
                target="_blank"
                rel="noreferrer"
                className="btn-primary"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "10px 18px",
                  fontSize: "13px",
                  textDecoration: "none",
                }}
              >
                <ExternalLink size={16} /> Open {telegramBotUsername} in Telegram
              </a>
              <button
                type="button"
                onClick={handleRefreshTelegramStatus}
                className="btn-secondary"
                style={{ padding: "10px 16px", fontSize: "13px" }}
              >
                <RefreshCw size={14} /> Refresh Connection Status
              </button>
            </div>
          </div>
        )}

        <div style={{ marginTop: "20px" }}>
          {telegramConnected ? (
            /* Connected View */
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "14px",
                padding: "16px",
                borderRadius: "12px",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div>
                <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Connected Account
                </div>
                <div style={{ fontSize: "15px", fontWeight: "800", color: "var(--accent-cyan)", marginTop: "4px" }}>
                  {telegramHandle || "Linked Telegram User"}
                </div>
                {telegramUserId && (
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                    Chat ID: <code>{telegramUserId}</code> · Notifications: <strong style={{ color: "var(--accent-primary)" }}>Active</strong>
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={handleDisconnectTelegram}
                disabled={telegramLoading}
                className="btn-secondary"
                style={{ color: "var(--status-blocked)", borderColor: "var(--status-blocked-border)", fontSize: "12px" }}
              >
                <Unlink size={14} /> Disconnect Telegram
              </button>
            </div>
          ) : (
            /* Unconnected View */
            <div
              style={{
                padding: "20px",
                borderRadius: "12px",
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border-subtle)",
                textAlign: "center",
              }}
            >
              <Smartphone size={32} color="var(--accent-cyan)" style={{ margin: "0 auto 12px" }} />
              <h3 style={{ fontSize: "16px", fontWeight: "800", color: "var(--text-white)", marginBottom: "6px" }}>
                Connect your Telegram account to Syncora AI
              </h3>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", maxWidth: "460px", margin: "0 auto 18px" }}>
                {!isPhoneVerified
                  ? "⚠️ Please complete phone number verification in the section above before connecting Telegram."
                  : "Generates a single-use secure linking token and connects your chat ID for task updates and AI assistance."}
              </p>
              <button
                type="button"
                onClick={handleConnectTelegram}
                disabled={!isPhoneVerified || telegramLoading}
                className="btn-primary"
                style={{
                  padding: "12px 24px",
                  fontSize: "14px",
                  fontWeight: "700",
                  opacity: !isPhoneVerified ? 0.5 : 1,
                  cursor: !isPhoneVerified ? "not-allowed" : "pointer",
                }}
              >
                {telegramLoading ? "Generating Token..." : "Connect Telegram"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ---------------- 4. BACKEND API SETTINGS CARD ---------------- */}
      <div className="card">
        <div className="section-label">INFRASTRUCTURE</div>
        <h2 className="section-title" style={{ marginBottom: "16px" }}>Backend API Connection</h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "6px" }}>
              FASTAPI BACKEND URL
            </label>
            <div style={{ display: "flex", gap: "10px" }}>
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                style={{
                  flex: 1,
                  padding: "10px 12px",
                  borderRadius: "8px",
                  backgroundColor: "var(--bg-app)",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-white)",
                  fontSize: "13px",
                }}
              />
              <button
                type="button"
                className="btn-secondary"
                onClick={() => alert(`Active Backend API Endpoint: ${apiUrl}`)}
                style={{ fontSize: "12px" }}
              >
                Ping Server
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
