import sqlite3
from pathlib import Path


DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "fitness.db"
PROFILE_MIGRATION = DB_DIR / "migrations" / "001_profile_intake.sql"

BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    username TEXT,
    age INTEGER,
    gender TEXT,
    height REAL,
    weight REAL,
    experience TEXT,
    goal TEXT DEFAULT '增肌',
    training_days INTEGER DEFAULT 3,
    default_training_days TEXT DEFAULT '周一,周三,周五',
    place TEXT,
    equipments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS injuries (
    injury_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    body_part TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS action_lib (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    target_muscle TEXT,
    equipment TEXT,
    gif_url TEXT,
    tags TEXT
);

CREATE TABLE IF NOT EXISTS plan_exercises (
    plan_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    training_date DATE NOT NULL,
    action_id INTEGER NOT NULL,
    order_num INTEGER,
    sets INTEGER,
    reps INTEGER,
    rest TEXT,
    weight_suggestion TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (action_id) REFERENCES action_lib(action_id)
);

CREATE TABLE IF NOT EXISTS training_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    training_date DATE NOT NULL,
    action_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('已完成', '未完成', '部分完成')),
    note TEXT,
    is_manually_modified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (action_id) REFERENCES action_lib(action_id)
);
"""


def init_database() -> None:
    connection = sqlite3.connect(str(DB_PATH))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(BASE_SCHEMA)
        connection.executescript(PROFILE_MIGRATION.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()
    print(f"Database initialized: {DB_PATH}")


if __name__ == "__main__":
    init_database()
