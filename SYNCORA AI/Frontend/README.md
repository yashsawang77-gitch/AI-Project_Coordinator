# Syncora AI — Task Coordination, Phone Verification & Telegram AI Assistant

> **Every Task Connected. Every Blocker Detected.**  
> AI-powered team project coordination platform built for high-velocity hackathon teams.

---

## 🌟 Platform Capabilities

1. **Simple Authentication**: Streamlined sign in with username/email and password, show/hide password, and separate registration page.
2. **Real Phone OTP Verification**: Cellular SMS OTP verification with country code selector, rate-limiting, 5-minute expiry, and honest dev sandbox fallback.
3. **Secure Telegram Account Linking**: Cryptographic single-use token deep link (`t.me/Bot?start=TOKEN`) requiring verified phone number.
4. **Website AI Assistant Chatbox**: Responsive floating chat panel grounded directly in SQLite task, deadline, blocker, and workload records.
5. **Real Telegram Bot**: Official Telegram Bot API supporting `/start`, `/help`, `/menu`, `/mytasks`, `/deadlines`, `/blocker`, `/myprogress`, `/teamstatus`, `/settings`, `/cancel`, interactive inline buttons, and natural language AI answers.
6. **Two-Way Synchronization**: Actions performed in Telegram (completing tasks, reporting blockers) update the website in real time, and website assignments trigger real Telegram notifications.
7. **Professional Demonstration Mode**: Pristine demo workspace with pre-seeded personas (Maya Chen, Alex Morgan, Leo Park, Nina Shah), realistic task distributions, overdue items, blockers, and 12-step guided judge walkthrough.

---

## 🚀 Quick Setup & Installation

### 1. Backend Setup (FastAPI + SQLite)

```bash
cd backend

# Create or activate virtual environment (optional)
# python -m venv venv && source venv/bin/activate  (or venv\Scripts\activate on Windows)

# Install backend dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

Edit `backend/.env` with your credentials:
```env
# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_NAME=@SyncoraAIBot
TELEGRAM_BOT_USERNAME=SyncoraAIBot

# Set to true for live local polling without reverse proxy/ngrok
TELEGRAM_ENABLE_POLLING=true

# Phone Verification: "dev" (sandbox) or "twilio"
SMS_PROVIDER=dev
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Optional external LLM (system uses grounded SQLite engine when left blank)
GEMINI_API_KEY=
OPENAI_API_KEY=
```

Start the backend server:
```bash
python run_server.py
# Server runs on http://localhost:8000 (API docs at http://localhost:8000/docs)
```

---

### 2. Frontend Setup (React + Vite)

```bash
# In the Frontend root directory
npm install
npm run dev
# The website runs on http://localhost:3000/
```

To run a production build:
```bash
npm run build
npm run preview
```

---

## 🤖 Telegram Bot Configuration

### Step 1: Create Your Bot on Telegram
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts to choose a bot name and username (e.g. `MySyncoraBot`).
3. BotFather will provide an API token (e.g. `7891234567:AAHxyz...`).
4. Paste this token into `backend/.env`:
   ```env
   TELEGRAM_BOT_TOKEN=7891234567:AAHxyz...
   TELEGRAM_BOT_NAME=@MySyncoraBot
   TELEGRAM_BOT_USERNAME=MySyncoraBot
   TELEGRAM_ENABLE_POLLING=true
   ```
5. Restart the backend server. The bot will automatically start listening via long polling.

### Step 2: Available Bot Commands
- `/start` — Welcome message and 1-click account linking (`/start SYNC_TOKEN`).
- `/help` — Full command list and natural language tips.
- `/menu` — Interactive inline button menu.
- `/mytasks` — View assigned tasks with 1-click **Complete** and **Report Blocker** buttons.
- `/deadlines` — Overdue and upcoming deadline breakdown.
- `/blocker [reason]` — Flag an urgent roadblock to your team lead.
- `/myprogress` — Personal sprint stats and capacity utilization.
- `/teamstatus` — Team-wide workload audit (restricted to Team Leaders).
- `/settings` — Account status and disconnect option.
- `/cancel` — Abort active multi-step conversation.

---

## 📱 Phone Number OTP Verification Workflow

1. Navigate to **Profile Settings** on the website.
2. Under **Phone Number OTP Verification**:
   - Choose your country code (default `+91 India`, `+1 US`, `+44 UK`, etc.).
   - Enter your phone number.
   - Click **Send OTP**.
3. If using Twilio, an actual cellular SMS is dispatched. In `dev` sandbox mode, the 6-digit OTP is securely logged and disclosed in the sandbox panel.
4. Enter the 6-digit OTP and click **Verify OTP**.
5. Once verified, the database updates `is_phone_verified = 1`, and the **Connect Telegram** button becomes enabled.

---

## 🔗 Secure Telegram Account Linking Workflow

1. After phone verification, scroll to the **Telegram Integration** card in Settings.
2. Click **Connect Telegram**.
3. The backend generates a cryptographically secure, 10-minute, single-use linking token and opens:
   `https://t.me/YOUR_BOT_USERNAME?start=SYNC_TOKEN`
4. Tap **Start** in Telegram.
5. The bot validates the token against SQLite, binds your Telegram user ID & chat ID, and enables live task notifications.
6. The website immediately reflects the connected status.

---

## 🏆 12-Step Hackathon Judge Demonstration Walkthrough

Click **"Judge Walkthrough Guide"** in the top demo banner to view the sequence:

1. **Sign in to Syncora AI**: Click **Team Leader (Maya Chen)** for 1-click demo access.
2. **Open Leader Dashboard**: Inspect KPI numbers, donut chart distribution, and team pulse capacity.
3. **Assign a Task**: Click `+ Create Task` and assign work to **Alex Morgan**.
4. **Telegram Notification**: Alex receives an instant assignment alert with priority and deadline in Telegram.
5. **Inspect Tasks in Telegram**: In Telegram, send `/mytasks` to view assigned work.
6. **Mark Complete from Telegram**: Tap `✓ Complete` inline button in Telegram.
7. **Website Live Sync**: The website updates the task status to **Completed** automatically.
8. **Report a Blocker via Telegram**: Send `/blocker Waiting on staging database credentials`.
9. **Blocker Appears on Website**: The task displays a red accent bar, and a critical notification is logged for the leader.
10. **Open Website AI Chatbox**: Click the floating **Ask Syncora AI** button in the bottom right corner.
11. **Ask Grounded Question**: Click the prompt chip **"Which tasks are overdue?"**.
12. **Grounded Answer**: Assistant cites `SYNC-198 (Resolve payment webhook errors)` directly from SQLite records.

---

## 🧪 Automated Testing

### Backend & Integration Test Suite (38 Tests)
```bash
python backend/tests/test_full_platform.py
```
Validates:
- Database seeding and demo reset
- Authentication, registration, and password reset
- Phone OTP requesting, rate-limiting, and verification
- Telegram deep linking, verification, and chat ID binding
- All Telegram slash commands and callbacks
- Grounded AI Coordinator responses
- Two-way data synchronization

### Frontend & Design Token Test Suite (36 Tests)
```bash
node test-all-features.mjs
```
Validates:
- Mock store integrity and API fallbacks
- Task creation, blocker reporting, and workload rebalancing
- Role switcher and visual styling contracts

---

## 🔒 Security Architecture

- **No Secrets in Frontend**: Telegram bot tokens, AI API keys, and Twilio secrets reside exclusively in backend environment variables.
- **Role-Based Authorization**: Full team workload distribution and reassignment approval are restricted to Team Leaders.
- **Cryptographic Linking Tokens**: High-entropy single-use tokens expiring in 10 minutes prevent account hijacking.
- **Anti-Spam & Rate Limiting**: OTP requests are bounded to 3 requests per 10 minutes with max 3 verification attempts.
- **Safe Fallback Disclosures**: Never claims an SMS was sent if external credentials are unconfigured; clearly discloses sandbox mode.
