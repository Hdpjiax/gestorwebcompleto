from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, profile_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[profile_id].add(websocket)
        await websocket.send_json(
            {
                "type": "connected",
                "profile_id": profile_id,
                "message": "Flow event stream connected.",
            }
        )

    def disconnect(self, profile_id: int, websocket: WebSocket) -> None:
        self._connections[profile_id].discard(websocket)
        if not self._connections[profile_id]:
            self._connections.pop(profile_id, None)

    async def broadcast(self, profile_id: int, event_type: str, payload: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for websocket in list(self._connections.get(profile_id, set())):
            try:
                await websocket.send_json({"type": event_type, "profile_id": profile_id, "payload": payload})
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(profile_id, websocket)
