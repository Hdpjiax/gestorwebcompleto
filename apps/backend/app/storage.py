import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import AnonymityLevel, ProfileCreate, ProfileUpdate


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "backend.sqlite3"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteStore:
    def __init__(self, db_path: str | os.PathLike[str] | None = None) -> None:
        self.db_path = str(db_path or os.getenv("GESTOR_BACKEND_DB", DEFAULT_DB_PATH))
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._memory_connection: sqlite3.Connection | None = None
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._memory_connection is None:
                self._memory_connection = sqlite3.connect(self.db_path, check_same_thread=False)
                self._memory_connection.row_factory = sqlite3.Row
            return self._memory_connection

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    anonymity_level TEXT NOT NULL,
                    proxy TEXT,
                    camoufox_config TEXT NOT NULL,
                    is_running INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(profiles)").fetchall()}
            if "proxy" not in columns:
                conn.execute("ALTER TABLE profiles ADD COLUMN proxy TEXT")

    def list_profiles(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM profiles ORDER BY id ASC").fetchall()
            return [self._row_to_profile(row) for row in rows]

    def get_profile(self, profile_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
            return self._row_to_profile(row) if row else None

    def create_profile(self, payload: ProfileCreate) -> dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO profiles (
                    name, description, anonymity_level, proxy, camoufox_config, is_running, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    payload.name,
                    payload.description,
                    payload.anonymity_level.value,
                    payload.proxy.model_dump_json() if payload.proxy else None,
                    json.dumps(payload.camoufox_config),
                    now,
                    now,
                ),
            )
            profile_id = int(cursor.lastrowid)
        profile = self.get_profile(profile_id)
        if profile is None:
            raise RuntimeError("profile was not persisted")
        return profile

    def update_profile(self, profile_id: int, payload: ProfileUpdate) -> dict[str, Any] | None:
        current = self.get_profile(profile_id)
        if current is None:
            return None

        values = payload.model_dump(exclude_unset=True)
        if not values:
            return current

        fields: list[str] = []
        params: list[Any] = []
        for key, value in values.items():
            fields.append(f"{key} = ?")
            if key == "camoufox_config":
                params.append(json.dumps(value or {}))
            elif key == "proxy":
                params.append(value.model_dump_json() if value else None)
            elif key == "anonymity_level" and isinstance(value, AnonymityLevel):
                params.append(value.value)
            else:
                params.append(value)

        fields.append("updated_at = ?")
        params.append(utc_now_iso())
        params.append(profile_id)

        with self._connect() as conn:
            conn.execute(f"UPDATE profiles SET {', '.join(fields)} WHERE id = ?", params)
        return self.get_profile(profile_id)

    def delete_profile(self, profile_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            return cursor.rowcount > 0

    def set_running(self, profile_id: int, is_running: bool) -> dict[str, Any] | None:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE profiles SET is_running = ?, updated_at = ? WHERE id = ?",
                (1 if is_running else 0, utc_now_iso(), profile_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_profile(profile_id)

    def set_anonymity_level(self, profile_id: int, level: AnonymityLevel) -> dict[str, Any] | None:
        return self.update_profile(profile_id, ProfileUpdate(anonymity_level=level))

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["camoufox_config"] = json.loads(data["camoufox_config"])
        data["proxy"] = json.loads(data["proxy"]) if data.get("proxy") else None
        data["is_running"] = bool(data["is_running"])
        return data
