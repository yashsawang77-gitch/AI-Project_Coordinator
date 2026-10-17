import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Syncora UI Runtime Error caught by ErrorBoundary:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    localStorage.clear();
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            backgroundColor: "var(--bg-app)",
            color: "var(--text-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            fontFamily: "Inter, sans-serif",
          }}
        >
          <div
            style={{
              maxWidth: "520px",
              width: "100%",
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--status-blocked-border)",
              borderRadius: "16px",
              padding: "32px",
              textAlign: "center",
              boxShadow: "var(--shadow-modal)",
            }}
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                borderRadius: "50%",
                backgroundColor: "var(--status-blocked-bg)",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--status-blocked)",
                marginBottom: "16px",
              }}
            >
              <AlertTriangle size={28} />
            </div>
            <h2 style={{ fontSize: "22px", fontWeight: "700", color: "var(--text-white)", marginBottom: "8px" }}>
              Application Render Notice
            </h2>
            <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "20px", lineHeight: "1.5" }}>
              Syncora AI caught an unexpected interface state. Click below to safely reset cache and restore dashboard view.
            </p>
            {this.state.error && (
              <pre
                style={{
                  backgroundColor: "var(--bg-app)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "8px",
                  padding: "12px",
                  fontSize: "12px",
                  color: "var(--status-blocked)",
                  textAlign: "left",
                  overflowX: "auto",
                  marginBottom: "20px",
                  maxHeight: "140px",
                }}
              >
                {this.state.error.toString()}
              </pre>
            )}
            <button
              type="button"
              onClick={this.handleReset}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                backgroundColor: "var(--accent-primary)",
                color: "#ffffff",
                fontWeight: "700",
                fontSize: "15px",
                padding: "10px 20px",
                borderRadius: "10px",
                border: "none",
                cursor: "pointer",
              }}
            >
              <RefreshCw size={16} /> Reset & Reload App
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

