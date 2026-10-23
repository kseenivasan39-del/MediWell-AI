import sqlite3
import os

def migrate_database():
    db_path = "mediwell.db"
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check if updated_at exists on habit_logs
    cur.execute("PRAGMA table_info(habit_logs)")
    columns = [col[1] for col in cur.fetchall()]
    if "updated_at" not in columns:
        print("Migrating habit_logs: Adding updated_at column...")
        cur.execute("ALTER TABLE habit_logs ADD COLUMN updated_at DATETIME")
        conn.commit()

    # Check unique index
    cur.execute("PRAGMA index_list(habit_logs)")
    indexes = [idx[1] for idx in cur.fetchall()]
    if "uq_patient_habit_log_date" not in indexes:
        print("Migrating habit_logs: Adding unique index uq_patient_habit_log_date...")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_patient_habit_log_date ON habit_logs (patient_id, habit_id, log_date)")
        conn.commit()

    # Migrate drift_events columns
    cur.execute("PRAGMA table_info(drift_events)")
    drift_columns = [col[1] for col in cur.fetchall()]
    new_drift_cols = [
        ("plan_id", "INTEGER"),
        ("relative_change_pct", "FLOAT"),
        ("baseline_start_date", "DATE"),
        ("baseline_end_date", "DATE"),
        ("recent_start_date", "DATE"),
        ("recent_end_date", "DATE"),
        ("baseline_eligible", "INTEGER"),
        ("baseline_completed", "INTEGER"),
        ("recent_eligible", "INTEGER"),
        ("recent_completed", "INTEGER"),
        ("contributing_factors", "JSON"),
    ]
    for col_name, col_type in new_drift_cols:
        if col_name not in drift_columns:
            print(f"Migrating drift_events: Adding {col_name} column...")
            cur.execute(f"ALTER TABLE drift_events ADD COLUMN {col_name} {col_type}")
            conn.commit()

    # Check recovery_proposals table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recovery_proposals'")
    if not cur.fetchone():
        print("Creating recovery_proposals table...")
        cur.execute("""
            CREATE TABLE recovery_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
                plan_id INTEGER NOT NULL REFERENCES wellness_plans(id) ON DELETE CASCADE,
                drift_event_id INTEGER REFERENCES drift_events(id) ON DELETE SET NULL,
                title VARCHAR(128) NOT NULL,
                rationale TEXT NOT NULL,
                status VARCHAR(32) NOT NULL DEFAULT 'pending',
                decision_notes TEXT,
                proposed_adjustments JSON NOT NULL DEFAULT '[]',
                user_revised_targets JSON,
                barrier_question VARCHAR(256),
                created_at DATETIME NOT NULL,
                decided_at DATETIME
            )
        """)
        cur.execute("CREATE INDEX idx_recovery_proposals_patient ON recovery_proposals (patient_id)")
        cur.execute("CREATE INDEX idx_recovery_proposals_plan ON recovery_proposals (plan_id)")
        conn.commit()

    # Check calendar_integrations table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_integrations'")
    if not cur.fetchone():
        print("Creating calendar_integrations table...")
        cur.execute("""
            CREATE TABLE calendar_integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(32) NOT NULL DEFAULT 'google',
                account_email VARCHAR(256),
                calendar_id VARCHAR(128) NOT NULL DEFAULT 'primary',
                encrypted_access_token TEXT,
                encrypted_refresh_token TEXT,
                token_expiry DATETIME,
                scope VARCHAR(256),
                is_connected BOOLEAN NOT NULL DEFAULT 0,
                connected_at DATETIME,
                last_synced_at DATETIME,
                last_sync_status VARCHAR(64),
                last_sync_error TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        conn.commit()

    # Check calendar_event_mappings table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_event_mappings'")
    if not cur.fetchone():
        print("Creating calendar_event_mappings table...")
        cur.execute("""
            CREATE TABLE calendar_event_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL REFERENCES wellness_goals(id) ON DELETE CASCADE,
                patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
                google_event_id VARCHAR(256) NOT NULL,
                calendar_id VARCHAR(128) NOT NULL DEFAULT 'primary',
                event_title VARCHAR(256) NOT NULL,
                scheduled_time VARCHAR(64) NOT NULL,
                timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Kolkata',
                sync_status VARCHAR(32) NOT NULL DEFAULT 'synced',
                last_synced_at DATETIME NOT NULL,
                CONSTRAINT uq_goal_calendar_mapping UNIQUE (goal_id, calendar_id)
            )
        """)
        cur.execute("CREATE INDEX idx_cal_event_mappings_goal ON calendar_event_mappings (goal_id)")
        cur.execute("CREATE INDEX idx_cal_event_mappings_patient ON calendar_event_mappings (patient_id)")
        cur.execute("CREATE INDEX idx_cal_event_mappings_event ON calendar_event_mappings (google_event_id)")
        conn.commit()

    conn.close()
    print("Database migration completed successfully.")

if __name__ == "__main__":
    migrate_database()
