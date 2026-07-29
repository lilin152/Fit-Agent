-- Profile intake extension. Safe to run multiple times for table creation.

CREATE TABLE IF NOT EXISTS improvement_areas (
    improvement_area_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    body_part TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS profile_change_log (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- SQLite cannot add multiple columns in one statement and does not support
-- IF NOT EXISTS on ADD COLUMN in older runtimes. The repository initializer
-- performs column-level idempotency checks before applying these changes.

