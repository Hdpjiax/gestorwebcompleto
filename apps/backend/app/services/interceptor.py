from ..models import HttpFlow, HttpFlowCreate, InterceptedRequest, ReplayRequest
from ..storage import SQLiteStore


SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "proxy-authorization"}


class InterceptorService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def record_flow(self, payload: HttpFlowCreate) -> HttpFlow:
        redacted = payload.model_copy(
            update={
                "request_headers": self._redact_headers(payload.request_headers),
                "response_headers": self._redact_headers(payload.response_headers),
                "replayable": payload.in_scope,
            }
        )
        return HttpFlow.model_validate(self.store.create_http_flow(redacted))

    def list_flows(self, profile_id: int | None = None) -> list[HttpFlow]:
        return [HttpFlow.model_validate(row) for row in self.store.list_http_flows(profile_id)]

    def list_request_rows(self, profile_id: int | None = None) -> list[InterceptedRequest]:
        rows: list[InterceptedRequest] = []
        for flow in self.list_flows(profile_id):
            rows.append(
                InterceptedRequest(
                    id=flow.id,
                    method=flow.method.upper(),
                    host=flow.host,
                    path=flow.path,
                    status=flow.status_code or 0,
                    type=flow.resource_type,
                    profile=str(flow.profile_id),
                    time=flow.captured_at.strftime("%H:%M:%S"),
                )
            )
        return rows

    def replay(self, flow_id: str, payload: ReplayRequest | None = None) -> dict[str, str]:
        flow = self.store.get_http_flow(flow_id)
        if flow is None:
            return {"status": "missing", "detail": "Flow not found"}
        if not flow["in_scope"] or not flow["replayable"]:
            return {"status": "blocked", "detail": "Replay blocked because the flow is out of scope"}

        changes = payload.model_dump(exclude_none=True) if payload else {}
        return {
            "status": "stubbed",
            "detail": f"Replay validated for {flow['method']} {flow['host']}{flow['path']} with {len(changes)} override(s).",
        }

    @staticmethod
    def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
        return {
            key: "[redacted]" if key.lower() in SENSITIVE_HEADERS else value
            for key, value in headers.items()
        }
