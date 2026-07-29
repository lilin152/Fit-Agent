"""SQLite persistence for user body profiles."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


class ProfileRepository:
    def __init__(self, database_path: Path | str):
        self.database_path = Path(database_path)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.database_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create new tables and safely extend the project's existing schema."""

        with self._connect() as connection:
            connection.executescript(
                """
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
                    goal TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS injuries (
                    injury_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    body_part TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

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
                """
            )

            self._add_column(connection, "users", "description", "TEXT")
            self._add_column(connection, "users", "experience_level", "TEXT")
            self._add_column(connection, "users", "assessment_status", "TEXT DEFAULT 'pending'")
            self._add_column(connection, "users", "updated_at", "TEXT")
            self._add_column(connection, "users", "version", "INTEGER DEFAULT 1")

            self._add_column(connection, "injuries", "side", "TEXT DEFAULT 'unknown'")
            self._add_column(connection, "injuries", "status", "TEXT DEFAULT 'unknown'")
            self._add_column(connection, "injuries", "pain_score", "INTEGER")
            self._add_column(connection, "injuries", "trigger_movements", "TEXT")
            self._add_column(connection, "injuries", "doctor_restrictions", "TEXT")
            self._add_column(connection, "injuries", "updated_at", "TEXT")

            now = _utc_now()
            connection.execute(
                "UPDATE users SET updated_at = COALESCE(updated_at, created_at, ?), "
                "version = COALESCE(version, 1), assessment_status = COALESCE(assessment_status, 'pending')",
                (now,),
            )
            connection.execute(
                "UPDATE injuries SET updated_at = COALESCE(updated_at, created_at, ?), "
                "side = COALESCE(side, 'unknown'), status = COALESCE(status, 'unknown')",
                (now,),
            )
            connection.commit()

    @staticmethod
    def _add_column(
        connection: sqlite3.Connection, table: str, column: str, definition: str
    ) -> None:
        existing = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def user_exists(self, user_id: int) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return row is not None

    def list_users(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT user_id, email, username FROM users ORDER BY user_id"
            ).fetchall()
            return [dict(row) for row in rows]

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            user = connection.execute(
                """
                SELECT user_id, age, gender, height, weight, experience, goal,
                       description, experience_level, assessment_status,
                       created_at, updated_at, version
                FROM users WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
            if user is None:
                return None

            injuries = connection.execute(
                """
                SELECT body_part, side, status, pain_score, trigger_movements,
                       doctor_restrictions, description
                FROM injuries WHERE user_id = ? ORDER BY injury_id
                """,
                (user_id,),
            ).fetchall()
            improvements = connection.execute(
                """
                SELECT body_part, description
                FROM improvement_areas
                WHERE user_id = ? ORDER BY improvement_area_id
                """,
                (user_id,),
            ).fetchall()

        history = _json_load(user["experience"], None)
        if not isinstance(history, dict):
            history = {"summary": user["experience"]} if user["experience"] else None

        goals = _json_load(user["goal"], None)
        if not isinstance(goals, list):
            goals = [user["goal"]] if user["goal"] else None

        sex_mapping = {"男": "male", "女": "female"}
        sex = sex_mapping.get(user["gender"], user["gender"] or None)

        return {
            "user_id": user["user_id"],
            "sex": sex,
            "age": user["age"],
            "height_cm": user["height"],
            "weight_kg": user["weight"],
            "exercise_history": history,
            "experience_level": user["experience_level"] or "unknown",
            "goals": goals,
            "improvement_areas": [dict(row) for row in improvements],
            "injuries": [
                {
                    **dict(row),
                    "trigger_movements": _json_load(row["trigger_movements"], []),
                }
                for row in injuries
            ],
            "description": user["description"],
            "assessment_status": user["assessment_status"] or "pending",
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
            "version": user["version"] or 1,
        }

    def save_profile(
        self,
        user_id: int,
        profile: dict[str, Any],
        *,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        current = self.get_profile(user_id)
        if current is None:
            raise ValueError(f"User {user_id} does not exist")

        current_version = int(current.get("version") or 1)
        if expected_version is not None and expected_version != current_version:
            raise ValueError(
                f"Profile version conflict: expected {expected_version}, current {current_version}"
            )

        new_version = current_version + 1
        now = _utc_now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            latest = connection.execute(
                "SELECT version FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            latest_version = int(latest["version"] or 1)
            if latest_version != current_version:
                raise ValueError("Profile changed during this update; reload and try again")

            connection.execute(
                """
                UPDATE users
                SET age = ?, gender = ?, height = ?, weight = ?, experience = ?,
                    experience_level = ?, goal = ?, description = ?,
                    assessment_status = ?, updated_at = ?, version = ?
                WHERE user_id = ?
                """,
                (
                    profile.get("age"),
                    profile.get("sex"),
                    profile.get("height_cm"),
                    profile.get("weight_kg"),
                    _json_dump(profile.get("exercise_history")),
                    profile.get("experience_level", "unknown"),
                    _json_dump(profile.get("goals") or []),
                    profile.get("description"),
                    profile.get("assessment_status", "pending"),
                    now,
                    new_version,
                    user_id,
                ),
            )

            connection.execute("DELETE FROM injuries WHERE user_id = ?", (user_id,))
            for injury in profile.get("injuries") or []:
                connection.execute(
                    """
                    INSERT INTO injuries (
                        user_id, body_part, side, status, pain_score,
                        trigger_movements, doctor_restrictions, description,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        injury["body_part"],
                        injury.get("side", "unknown"),
                        injury.get("status", "unknown"),
                        injury.get("pain_score"),
                        _json_dump(injury.get("trigger_movements") or []),
                        injury.get("doctor_restrictions"),
                        injury.get("description"),
                        now,
                        now,
                    ),
                )

            connection.execute(
                "DELETE FROM improvement_areas WHERE user_id = ?", (user_id,)
            )
            for area in profile.get("improvement_areas") or []:
                connection.execute(
                    """
                    INSERT INTO improvement_areas (
                        user_id, body_part, description, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, area["body_part"], area.get("description"), now, now),
                )

            ignored_audit_fields = {"updated_at", "version", "created_at"}
            for field_name, new_value in profile.items():
                if field_name in ignored_audit_fields or field_name == "user_id":
                    continue
                old_value = current.get(field_name)
                if old_value != new_value:
                    connection.execute(
                        """
                        INSERT INTO profile_change_log (
                            user_id, field_name, old_value, new_value, created_at
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            field_name,
                            _json_dump(old_value),
                            _json_dump(new_value),
                            now,
                        ),
                    )

            connection.commit()

        saved = self.get_profile(user_id)
        if saved is None:
            raise RuntimeError("Profile disappeared after save")
        return saved

