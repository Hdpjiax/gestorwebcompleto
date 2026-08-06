import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import AnonymityLevel, HttpFlowCreate, ProfileCreate, ProfileUpdate


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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS http_flows (
                    id TEXT PRIMARY KEY,
                    profile_id INTEGER NOT NULL,
                    method TEXT NOT NULL,
                    scheme TEXT NOT NULL,
                    host TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER,
                    request_headers TEXT NOT NULL,
                    response_headers TEXT NOT NULL,
                    request_body_preview TEXT,
                    response_body_preview TEXT,
                    resource_type TEXT NOT NULL,
                    in_scope INTEGER NOT NULL,
                    replayable INTEGER NOT NULL,
                    intercept_decision TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
                )
                """
            )

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

    def create_http_flow(self, payload: HttpFlowCreate) -> dict[str, Any]:
        flow_id = f"flow-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        captured_at = utc_now_iso()
        replayable = bool(payload.in_scope)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO http_flows (
                    id, profile_id, method, scheme, host, path, status_code,
                    request_headers, response_headers, request_body_preview, response_body_preview,
                    resource_type, in_scope, replayable, intercept_decision, captured_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    flow_id,
                    payload.profile_id,
                    payload.method.upper(),
                    payload.scheme,
                    payload.host,
                    payload.path,
                    payload.status_code,
                    json.dumps(payload.request_headers),
                    json.dumps(payload.response_headers),
                    payload.request_body_preview,
                    payload.response_body_preview,
                    payload.resource_type,
                    1 if payload.in_scope else 0,
                    1 if replayable else 0,
                    "forward" if payload.in_scope else "out_of_scope",
                    captured_at,
                ),
            )
        flow = self.get_http_flow(flow_id)
        if flow is None:
            raise RuntimeError("flow was not persisted")
        return flow

    def list_http_flows(self, profile_id: int | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if profile_id is None:
                rows = conn.execute("SELECT * FROM http_flows ORDER BY captured_at DESC").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM http_flows WHERE profile_id = ? ORDER BY captured_at DESC",
                    (profile_id,),
                ).fetchall()
            return [self._row_to_http_flow(row) for row in rows]

    def get_http_flow(self, flow_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM http_flows WHERE id = ?", (flow_id,)).fetchone()
            return self._row_to_http_flow(row) if row else None

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["camoufox_config"] = json.loads(data["camoufox_config"])
        data["proxy"] = json.loads(data["proxy"]) if data.get("proxy") else None
        data["is_running"] = bool(data["is_running"])
        return data

    @staticmethod
    def _row_to_http_flow(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["request_headers"] = json.loads(data["request_headers"])
        data["response_headers"] = json.loads(data["response_headers"])
        data["in_scope"] = bool(data["in_scope"])
        data["replayable"] = bool(data["replayable"])
        return data
