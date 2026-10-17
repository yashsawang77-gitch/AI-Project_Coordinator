"""
Syncora AI - Shared SQLite Database & Schema Manager
Acts as the single source of truth for projects, members, tasks, telegram bindings,
activity logs, AI metrics, notifications, and workload recommendations.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import settings

def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row factory configured."""
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(force_reseed: bool = False):
    """Initializes tables and seeds starting data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Team Members / Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        initials TEXT NOT NULL,
        role TEXT NOT NULL,
        title TEXT NOT NULL,
        avatar_bg TEXT NOT NULL,
        avatar_color TEXT NOT NULL DEFAULT '#ffffff',
        online INTEGER NOT NULL DEFAULT 1,
        active_tasks INTEGER NOT NULL DEFAULT 0,
        completion_rate INTEGER NOT NULL DEFAULT 80,
        workload INTEGER NOT NULL DEFAULT 50,
        workload_status TEXT NOT NULL DEFAULT 'Optimal',
        workload_color TEXT NOT NULL DEFAULT '#18e5b4',
        email TEXT UNIQUE NOT NULL,
        telegram_handle TEXT,
        telegram_user_id TEXT UNIQUE,
        telegram_chat_id TEXT,
        telegram_connected INTEGER NOT NULL DEFAULT 0,
        available_capacity_hours REAL DEFAULT 35.0,
        skills TEXT NOT NULL DEFAULT 'General',
        created_at TEXT NOT NULL
    );
    """)

    # Run member migrations safely if existing db
    for col, ctype in [
        ("available_capacity_hours", "REAL NOT NULL DEFAULT 35.0"),
        ("skills", "TEXT NOT NULL DEFAULT 'General'"),
        ("phone_number", "TEXT"),
        ("is_phone_verified", "INTEGER NOT NULL DEFAULT 0"),
        ("phone_verified_at", "TEXT"),
        ("password_hash", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE members ADD COLUMN {col} {ctype};")
        except Exception:
            pass

    # 3. Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        project TEXT NOT NULL,
        assignee_id TEXT,
        assignee_name TEXT NOT NULL,
        assignee_initials TEXT NOT NULL,
        assignee_bg TEXT NOT NULL DEFAULT '#18e5b4',
        assignee_text_color TEXT NOT NULL DEFAULT '#090d16',
        deadline TEXT NOT NULL,
        deadline_status TEXT NOT NULL DEFAULT 'upcoming',
        status TEXT NOT NULL DEFAULT 'In Progress',
        priority TEXT NOT NULL DEFAULT 'Medium',
        left_bar_color TEXT NOT NULL DEFAULT '#f59e0b',
        estimated_hours TEXT NOT NULL DEFAULT '8h',
        confidence TEXT NOT NULL DEFAULT '85%',
        blocker_reason TEXT,
        description TEXT,
        estimated_remaining_hours REAL NOT NULL DEFAULT 8.0,
        explicit_estimate_hours REAL,
        depends_on TEXT NOT NULL DEFAULT '',
        deadline_date TEXT,
        subtasks TEXT NOT NULL DEFAULT '[]',
        completed_work TEXT,
        remaining_work TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (assignee_id) REFERENCES members (id) ON DELETE SET NULL
    );
    """)

    # Run task migrations safely if existing db
    for col, ctype in [
        ("estimated_remaining_hours", "REAL NOT NULL DEFAULT 8.0"),
        ("explicit_estimate_hours", "REAL"),
        ("depends_on", "TEXT NOT NULL DEFAULT ''"),
        ("deadline_date", "TEXT"),
        ("subtasks", "TEXT NOT NULL DEFAULT '[]'"),
        ("completed_work", "TEXT"),
        ("remaining_work", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col} {ctype};")
        except Exception:
            pass


    # 4. Telegram Account Linking Verification Codes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_codes (
        code TEXT PRIMARY KEY,
        member_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
    );
    """)

    # 5. Telegram Updates Log (for idempotency and retry handling)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telegram_updates (
        update_id INTEGER PRIMARY KEY,
        sender_id TEXT,
        chat_id TEXT,
        message_id INTEGER,
        message_text TEXT,
        parsed_action TEXT,
        processed_at TEXT NOT NULL
    );
    """)

    # 6. Activity / Intelligence Feed
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_feed (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        icon TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        time_ago TEXT NOT NULL,
        badge_text TEXT NOT NULL,
        badge_type TEXT NOT NULL,
        task_id TEXT,
        member_id TEXT,
        project_id TEXT,
        metadata TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 7. AI Metrics Counter
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_metrics (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        follow_ups_sent INTEGER NOT NULL DEFAULT 34,
        replies_received INTEGER NOT NULL DEFAULT 28,
        blockers_detected INTEGER NOT NULL DEFAULT 7,
        status_changes INTEGER NOT NULL DEFAULT 19,
        clarifications INTEGER NOT NULL DEFAULT 4,
        updated_at TEXT NOT NULL
    );
    """)

    # 8. Workload Recommendations (Invisible Workload Detector)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workload_recommendations (
        id TEXT PRIMARY KEY,
        priority TEXT NOT NULL,
        urgency_color TEXT NOT NULL,
        overburdened_member TEXT NOT NULL,
        current_load INTEGER NOT NULL,
        suggested_member TEXT NOT NULL,
        suggested_load INTEGER NOT NULL,
        task_id TEXT NOT NULL,
        task_title TEXT NOT NULL,
        task_project TEXT NOT NULL,
        task_estimated_hours TEXT NOT NULL,
        task_uncertainty TEXT,
        task_confidence TEXT NOT NULL,
        reasoning TEXT NOT NULL,
        action_proposed TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        source_member_id TEXT,
        recipient_member_id TEXT,
        workload_impact TEXT,
        relevant_constraints TEXT,
        assumptions TEXT,
        reviewed_by TEXT,
        reviewed_at TEXT,
        updated_at TEXT,
        approved INTEGER NOT NULL DEFAULT 0,
        rejected INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """)

    # Run workload_recommendations migrations safely
    for col, ctype in [
        ("status", "TEXT NOT NULL DEFAULT 'pending'"),
        ("source_member_id", "TEXT"),
        ("recipient_member_id", "TEXT"),
        ("workload_impact", "TEXT"),
        ("relevant_constraints", "TEXT"),
        ("assumptions", "TEXT"),
        ("reviewed_by", "TEXT"),
        ("reviewed_at", "TEXT"),
        ("updated_at", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE workload_recommendations ADD COLUMN {col} {ctype};")
        except Exception:
            pass

    # 9. Workload Alerts Deduplication Log (Prevents duplicate alerts for same unresolved risk)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workload_alerts_log (
        alert_key TEXT PRIMARY KEY,
        risk_type TEXT NOT NULL,
        member_id TEXT NOT NULL,
        leader_chat_id TEXT NOT NULL,
        message_text TEXT NOT NULL,
        sent_at TEXT NOT NULL
    );
    """)

    # 10. Leader Notifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        recipient_id TEXT,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        urgency TEXT NOT NULL DEFAULT 'Normal',
        is_read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """)

    # 11. Active Reminders Table (for outgoing pings and contextual reply resolution)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        member_id TEXT NOT NULL,
        telegram_chat_id TEXT NOT NULL,
        message_text TEXT NOT NULL,
        sent_at TEXT NOT NULL,
        replied INTEGER NOT NULL DEFAULT 0,
        replied_at TEXT,
        FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
    );
    """)

    # 12. Project Members Table (Role-based project authorization & membership checks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_members (
        project_id TEXT NOT NULL,
        member_id TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Member',
        joined_at TEXT NOT NULL,
        PRIMARY KEY (project_id, member_id),
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
    );
    """)

    # 13. Scheduler Distributed Leader Locks (Prevents duplicate instances in multi-worker setups)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scheduler_locks (
        lock_name TEXT PRIMARY KEY,
        holder_id TEXT NOT NULL,
        acquired_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    );
    """)

    # 14. Workload Snapshots Table (Caches workload state & detects staleness)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workload_snapshots (
        project_id TEXT PRIMARY KEY,
        snapshot_data TEXT NOT NULL,
        calculated_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    );
    """)

    # 15. Phone Number OTP Verifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS phone_verifications (
        id TEXT PRIMARY KEY,
        member_id TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        otp_hash TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        expires_at TEXT NOT NULL,
        verified INTEGER NOT NULL DEFAULT 0,
        verified_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
    );
    """)

    # 16. Unified AI Chat Messages History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_chat_messages (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        channel TEXT NOT NULL DEFAULT 'website',
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # Safe migration for activity_feed columns
    for col, ctype in [
        ("task_id", "TEXT"),
        ("member_id", "TEXT"),
        ("project_id", "TEXT"),
        ("metadata", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE activity_feed ADD COLUMN {col} {ctype};")
        except Exception:
            pass

    conn.commit()

    # Check if seed data is needed
    cursor.execute("SELECT COUNT(*) AS cnt FROM members;")
    members_count = cursor.fetchone()["cnt"]

    if members_count == 0 or force_reseed:
        seed_initial_data(conn, clear_all=force_reseed)

    conn.close()

def seed_initial_data(conn: sqlite3.Connection, clear_all: bool = False):
    """Populates database with high-fidelity seed records."""
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()

    if clear_all:
        cursor.execute("DELETE FROM reminders;")
        cursor.execute("DELETE FROM telegram_updates;")
        cursor.execute("DELETE FROM verification_codes;")
        cursor.execute("DELETE FROM activity_feed;")
        cursor.execute("DELETE FROM workload_recommendations;")
        cursor.execute("DELETE FROM notifications;")
        cursor.execute("DELETE FROM tasks;")
        cursor.execute("DELETE FROM members;")
        cursor.execute("DELETE FROM projects;")
        cursor.execute("DELETE FROM project_members;")
        cursor.execute("DELETE FROM scheduler_locks;")
        cursor.execute("DELETE FROM workload_snapshots;")

    # 1. Projects
    projects = [
        ("Marketing Launch", "Q4 campaign launch and strategic debut", now_str),
        ("Product Core", "Core UI design system, web dashboard and telegram bot integration", now_str),
        ("Infrastructure", "Backend microservices, webhook delivery and DB scaling", now_str),
        ("Growth", "Onboarding optimization, user retention and outbound sequences", now_str),
    ]
    for p in projects:
        cursor.execute("INSERT OR IGNORE INTO projects (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                       (p[0], p[0], p[1], p[2]))

    # 2. Members
    members = [
        (
            "mem-1", "Maya Chen", "MC", "Team Leader", "Team Lead",
            "#8b5cf6", "#ffffff", 1, 8, 76, 82, "Optimal", "#18e5b4",
            "maya.chen@novastudio.ai", "@mayachen_ai", "1001", "1001", 1, 35.0,
            "Team Leadership, Strategic Marketing, Product", now_str
        ),
        (
            "mem-2", "Alex Morgan", "AM", "Team Member", "Product Designer",
            "#06b6d4", "#ffffff", 1, 6, 82, 64, "Balanced", "#18e5b4",
            "alex.m@novastudio.ai", "@alexmorgan_ux", "1002", "1002", 1, 35.0,
            "UI/UX, Figma, Design Systems, Frontend", now_str
        ),
        (
            "mem-3", "Leo Park", "LP", "Team Member", "Backend Engineer",
            "#3b82f6", "#ffffff", 1, 7, 79, 92, "Overloaded", "#f59e0b",
            "leo.park@novastudio.ai", "@leopark_dev", "1003", "1003", 1, 30.0,
            "Backend, Python, FastAPI, Webhooks, Databases", now_str
        ),
        (
            "mem-4", "Nina Shah", "NS", "Team Member", "Growth Strategist",
            "#ec4899", "#ffffff", 1, 4, 88, 46, "Available", "#18e5b4",
            "nina.shah@novastudio.ai", "@ninashah_growth", "1004", "1004", 1, 40.0,
            "Growth, API Integrations, Webhooks, Documentation", now_str
        ),
    ]
    for m in members:
        cursor.execute("""
        INSERT OR REPLACE INTO members (
            id, name, initials, role, title, avatar_bg, avatar_color,
            online, active_tasks, completion_rate, workload, workload_status,
            workload_color, email, telegram_handle, telegram_user_id,
            telegram_chat_id, telegram_connected, available_capacity_hours, skills, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, m)

    # 2b. Project Memberships
    proj_members = [
        # Maya Chen (Team Leader) oversees all projects
        ("Marketing Launch", "mem-1", "Leader", now_str),
        ("Product Core", "mem-1", "Leader", now_str),
        ("Infrastructure", "mem-1", "Leader", now_str),
        ("Growth", "mem-1", "Leader", now_str),
        # Alex Morgan (Product Designer / Frontend)
        ("Product Core", "mem-2", "Member", now_str),
        ("Infrastructure", "mem-2", "Member", now_str),
        # Leo Park (Backend Engineer)
        ("Infrastructure", "mem-3", "Member", now_str),
        ("Product Core", "mem-3", "Member", now_str),
        # Nina Shah (Growth & Integrations)
        ("Growth", "mem-4", "Member", now_str),
        ("Infrastructure", "mem-4", "Member", now_str),
    ]
    for pm in proj_members:
        cursor.execute("""
            INSERT OR REPLACE INTO project_members (project_id, member_id, role, joined_at)
            VALUES (?, ?, ?, ?)
        """, pm)

    # 3. Tasks
    tasks = [
        (
            "SYNC-204", "Finalize Q4 campaign strategy", "Marketing Launch",
            "mem-1", "Maya Chen", "MC", "#18e5b4", "#090d16", "Today, 5:00 PM",
            "today", "In Progress", "High", "#f43f5e", "8-12h", "94%", None,
            "Prepare and align key performance indicators and media schedule for upcoming product debut.",
            10.0, 10.0, "", "2026-10-17T17:00:00Z", '["Finalize KPI metrics", "Review media schedule"]',
            "Drafted strategic outline", "Deck alignment", now_str, now_str
        ),
        (
            "SYNC-201", "Implement dashboard analytics", "Product Core",
            "mem-2", "Alex Morgan", "AM", "#18e5b4", "#090d16", "Tomorrow",
            "upcoming", "In Progress", "High", "#f43f5e", "14-18h", "88%", None,
            "Construct interactive visual widgets for task distribution and team pulse capacity tracking.",
            16.0, 16.0, "", "2026-10-18T18:00:00Z", '["Build donut charts", "Filter controls", "Pulse bars"]',
            "Charts prototype", "Filter validation", now_str, now_str
        ),
        (
            "SYNC-198", "Resolve payment webhook errors", "Infrastructure",
            "mem-3", "Leo Park", "LP", "#18e5b4", "#090d16", "2 days overdue",
            "overdue", "Blocked", "Critical", "#f43f5e", "10-16h", "72%",
            "Waiting for third-party production credentials and sandbox test environment setup.",
            "Fix intermittent timeout failures in payment gateway event handler.",
            14.0, 14.0, "", "2026-10-15T12:00:00Z", '["Inspect timeout logs", "Fix sandbox headers"]',
            "Log analysis", "Sandbox test environment", now_str, now_str
        ),
        (
            "SYNC-195", "Refresh onboarding email sequence", "Growth",
            "mem-4", "Nina Shah", "NS", "#18e5b4", "#090d16", "Oct 28",
            "normal", "Pending", "Medium", "#f59e0b", "6-8h", "91%", None,
            "Audit current conversion drop-off points and craft fresh automated copy.",
            7.0, 7.0, "", "2026-10-28T18:00:00Z", '["Audit drop-off points", "Draft automated copy"]',
            "Drop-off audit", "Copywriting", now_str, now_str
        ),
        (
            "SYNC-190", "Mobile navigation prototype", "Product Core",
            "mem-2", "Alex Morgan", "AM", "#18e5b4", "#090d16", "Completed Oct 23",
            "completed", "Completed", "High", "#3b82f6", "12h", "99%", None,
            "Create responsive drawer and gesture interaction design tokens in Figma.",
            0.0, 12.0, "", "2026-10-23T18:00:00Z", '["Drawer prototypes", "Gesture tokens"]',
            "All prototype tokens", "", now_str, now_str
        ),
        (
            "SYNC-187", "Update API documentation", "Infrastructure",
            "mem-2", "Alex Morgan", "AM", "#18e5b4", "#090d16", "Oct 30",
            "normal", "Pending", "Low", "#f59e0b", "4-6h", "85%", None,
            "Document new REST and WebSocket endpoint specifications for telegram bot integration.",
            5.0, 5.0, "SYNC-198", "2026-10-30T18:00:00Z", '["Document REST APIs", "Document Webhooks"]',
            "REST endpoints", "Webhook specifications", now_str, now_str
        ),
    ]
    for t in tasks:
        cursor.execute("""
        INSERT OR REPLACE INTO tasks (
            id, title, project, assignee_id, assignee_name, assignee_initials,
            assignee_bg, assignee_text_color, deadline, deadline_status,
            status, priority, left_bar_color, estimated_hours, confidence,
            blocker_reason, description, estimated_remaining_hours, explicit_estimate_hours,
            depends_on, deadline_date, subtasks, completed_work, remaining_work, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, t)

    # 4. Activity Feed
    activities = [
        ("act-1", "followup", "sparkle", "AI follow-up sent", "Asked Alex for an update on dashboard analytics", "2 min ago", "Delivered", "delivered", now_str, "SYNC-201"),
        ("act-2", "status_update", "check", "Status automatically updated", "Mobile navigation prototype → Completed", "18 min ago", "Verified", "verified", now_str, "SYNC-190"),
        ("act-3", "blocker_detected", "warning", "New blocker detected", "Leo needs production credentials for webhook testing", "43 min ago", "Needs attention", "attention", now_str, "SYNC-198"),
        ("act-4", "reply_interpreted", "sparkle", "Reply interpreted", "Nina confirmed email copy will be ready Thursday", "1 hr ago", "89% confidence", "confidence", now_str, "SYNC-195"),
    ]
    for a in activities:
        cursor.execute("""
        INSERT OR REPLACE INTO activity_feed (
            id, type, icon, title, description, time_ago, badge_text, badge_type, created_at, task_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, a)

    # 5. AI Metrics
    cursor.execute("""
    INSERT OR REPLACE INTO ai_metrics (
        id, follow_ups_sent, replies_received, blockers_detected, status_changes, clarifications, updated_at
    ) VALUES (1, 34, 28, 7, 19, 4, ?)
    """, (now_str,))

    # 6. Workload Recommendations
    rec_impact_1 = json.dumps({"sourceBefore": 92.0, "sourceAfter": 52.0, "recipientBefore": 46.0, "recipientAfter": 76.0, "effortHours": 14.0})
    rec_constraints_1 = json.dumps(["Skills Verified: Webhooks, Api Integrations", "Available Capacity: 40.0h recorded", "Projected Utilization: 76.0% (Safe < 85%)", "Project Membership: Infrastructure verified"])
    rec_assumptions_1 = json.dumps(["Task scope remains within 10-16h as documented.", "Nina Shah has access to Infrastructure credentials.", "External third-party sandbox is accessible."])

    rec_impact_2 = json.dumps({"sourceBefore": 64.0, "sourceAfter": 49.0, "recipientBefore": 46.0, "recipientAfter": 58.5, "effortHours": 5.0})
    rec_constraints_2 = json.dumps(["Skills Verified: Documentation, Api Integrations", "Available Capacity: 40.0h recorded", "Projected Utilization: 58.5% (Safe < 85%)", "Project Membership: Infrastructure verified"])
    rec_assumptions_2 = json.dumps(["Task scope remains within 4-6h as documented.", "Nina Shah completes onboarding sequence wrap-up first."])

    recs = [
        (
            "rec-1", "High Urgency", "#f43f5e", "Leo Park", 92, "Nina Shah", 46,
            "SYNC-198", "Resolve payment webhook errors", "Infrastructure",
            "10-16h (estimated)", "Moderate uncertainty due to third-party sandbox latency", "74%",
            "Leo currently has 7 active tasks and is blocked on production credentials, pushing active workload to 92%. Nina Shah has 46% capacity and expertise in webhook monitoring configurations.",
            "Reassign infrastructure webhook resolution from Leo Park to Nina Shah, reducing Leo's critical overload by ~18%.",
            "pending", "mem-3", "mem-4", rec_impact_1, rec_constraints_1, rec_assumptions_1,
            0, 0, now_str
        ),
        (
            "rec-2", "Preemptive", "#f59e0b", "Alex Morgan", 64, "Nina Shah", 46,
            "SYNC-187", "Update API documentation", "Infrastructure",
            "4-6h (estimated)", "Low uncertainty — scope is well-defined", "91%",
            "Alex Morgan has 21 estimated hours of remaining work and 35 recorded available hours before deadlines. The documentation task is suitable for reassignment to Nina Shah, subject to verified documentation skills and 40h working capacity checks.",
            "Shift API documentation to Nina Shah after onboarding sequence wrap-up.",
            "pending", "mem-2", "mem-4", rec_impact_2, rec_constraints_2, rec_assumptions_2,
            0, 0, now_str
        )
    ]
    for r in recs:
        cursor.execute("""
        INSERT OR REPLACE INTO workload_recommendations (
            id, priority, urgency_color, overburdened_member, current_load,
            suggested_member, suggested_load, task_id, task_title, task_project,
            task_estimated_hours, task_uncertainty, task_confidence,
            reasoning, action_proposed, status, source_member_id, recipient_member_id,
            workload_impact, relevant_constraints, assumptions, approved, rejected, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, r)

    # 7. Initial Notification
    cursor.execute("""
    INSERT OR REPLACE INTO notifications (
        id, recipient_id, type, title, message, urgency, is_read, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("notif-1", "mem-1", "blocker", "Critical Dependency Blocker", "Leo Park reported a block on SYNC-198: Third-party production credentials required.", "Critical", 0, now_str))

    conn.commit()
