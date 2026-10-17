"""
Syncora AI - Backend Configuration Service
Manages system configuration, environment variables, bot tokens, and runtime constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
ENV_PATH = BACKEND_DIR / ".env"

# Load environment variables if .env exists
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
else:
    # Also check frontend or parent .env
    load_dotenv(ROOT_DIR / ".env", override=True)

class Settings:
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    
    # Database
    DATABASE_PATH: Path = BACKEND_DIR / "syncora.db"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "MOCK_BOT_TOKEN_FOR_HACKATHON")
    TELEGRAM_BOT_NAME: str = os.getenv("TELEGRAM_BOT_NAME", "@SyncoraAIBot")
    TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", os.getenv("TELEGRAM_BOT_NAME", "SyncoraAIBot").lstrip("@"))
    TELEGRAM_LINKED_GROUP: str = os.getenv("TELEGRAM_LINKED_GROUP", "Nova Studio Core Team (Telegram)")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    TELEGRAM_POLLING_INTERVAL: float = float(os.getenv("TELEGRAM_POLLING_INTERVAL", "2.0"))
    TELEGRAM_ENABLE_POLLING: bool = os.getenv("TELEGRAM_ENABLE_POLLING", "false").lower() in ("true", "1", "yes")

    # Public URLs
    PUBLIC_WEBSITE_URL: str = os.getenv("PUBLIC_WEBSITE_URL", "http://localhost:3000")
    PUBLIC_BACKEND_URL: str = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")

    # SMS / Phone OTP Verification Configuration
    # Supported providers: "dev" (sandbox development provider), "twilio", "fast2sms"
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "dev").lower()
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    TWILIO_VERIFY_SERVICE_SID: str = os.getenv("TWILIO_VERIFY_SERVICE_SID", "")
    FAST2SMS_API_KEY: str = os.getenv("FAST2SMS_API_KEY", "")

    # AI / LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_CONFIDENCE_THRESHOLD: float = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.75"))

    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "syncora-college-hackathon-secret-key-2026")
    LINK_CODE_EXPIRE_SECONDS: int = int(os.getenv("LINK_CODE_EXPIRE_SECONDS", "600"))  # 10 minutes

    # Workload Thresholds (Configurable)
    OVERLOAD_THRESHOLD: int = int(os.getenv("OVERLOAD_THRESHOLD", "85"))
    UNDERLOAD_THRESHOLD: int = int(os.getenv("UNDERLOAD_THRESHOLD", "50"))
    OVERLOAD_UTILIZATION_THRESHOLD: float = float(os.getenv("OVERLOAD_UTILIZATION_THRESHOLD", "85.0"))
    UNDERLOAD_UTILIZATION_THRESHOLD: float = float(os.getenv("UNDERLOAD_UTILIZATION_THRESHOLD", "50.0"))
    ANALYSIS_WINDOW_DAYS: int = int(os.getenv("ANALYSIS_WINDOW_DAYS", "7"))
    HIGH_PRIORITY_DENSITY_THRESHOLD: int = int(os.getenv("HIGH_PRIORITY_DENSITY_THRESHOLD", "2"))
    OVERDUE_TASK_THRESHOLD: int = int(os.getenv("OVERDUE_TASK_THRESHOLD", "1"))
    DEADLINE_PRESSURE_HOURS: int = int(os.getenv("DEADLINE_PRESSURE_HOURS", "48"))

    # Scheduling & Proactive Analysis (Section 9)
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() in ("true", "1", "yes")
    REMINDERS_INTERVAL_SECONDS: int = int(os.getenv("REMINDERS_INTERVAL_SECONDS", "60"))
    WORKLOAD_ANALYSIS_INTERVAL_SECONDS: int = int(os.getenv("WORKLOAD_ANALYSIS_INTERVAL_SECONDS", "300"))
    BLOCKER_CHECK_INTERVAL_SECONDS: int = int(os.getenv("BLOCKER_CHECK_INTERVAL_SECONDS", "180"))
    DEADLINE_CHECK_INTERVAL_SECONDS: int = int(os.getenv("DEADLINE_CHECK_INTERVAL_SECONDS", "120"))
    STALE_SNAPSHOT_EXPIRY_MINUTES: int = int(os.getenv("STALE_SNAPSHOT_EXPIRY_MINUTES", "30"))
    REMINDER_MIN_COOLDOWN_HOURS: int = int(os.getenv("REMINDER_MIN_COOLDOWN_HOURS", "6"))
    SCHEDULER_LOCK_TTL_SECONDS: int = int(os.getenv("SCHEDULER_LOCK_TTL_SECONDS", "120"))
    LEADER_ALERT_MEANINGFUL_CHANGE_ONLY: bool = os.getenv("LEADER_ALERT_MEANINGFUL_CHANGE_ONLY", "true").lower() in ("true", "1", "yes")

settings = Settings()


