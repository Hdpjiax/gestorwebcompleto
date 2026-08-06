from fnmatch import fnmatch

from ..models import (
    FlowDecision,
    FlowDecisionRequest,
    HttpFlow,
    HttpFlowCreate,
    InterceptDecision,
    InterceptRule,
    InterceptRuleCreate,
    InterceptedRequest,
    ReplayRequest,
)
from ..storage import SQLiteStore


SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "proxy-authorization"}


class InterceptorService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def record_flow(self, payload: HttpFlowCreate) -> HttpFlow:
        profile = self.store.get_profile(payload.profile_id)
        in_scope = payload.in_scope and _host_allowed(payload.host, profile["allowed_hosts"] if profile else [])
        decision = InterceptDecision.out_of_scope
        if in_scope:
            decision = self._matching_decision(payload) or payload.intercept_decision
        redacted = payload.model_copy(
            update={
                "request_headers": _redact_headers(payload.request_headers),
                "response_headers": _redact_headers(payload.response_headers),
                "in_scope": in_scope,
                "replayable": in_scope,
                "intercept_decision": decision,
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

    def decide(self, flow_id: str, payload: FlowDecisionRequest) -> FlowDecision | None:
        flow = self.store.get_http_flow(flow_id)
        if flow is None:
            return None
        if not flow["in_scope"] and payload.decision != InterceptDecision.out_of_scope:
            payload = payload.model_copy(update={"decision": InterceptDecision.out_of_scope})
        return FlowDecision.model_validate(self.store.apply_flow_decision(flow_id, payload))

    def list_decisions(self, flow_id: str) -> list[FlowDecision]:
        return [FlowDecision.model_validate(row) for row in self.store.list_flow_decisions(flow_id)]

    def create_rule(self, payload: InterceptRuleCreate) -> InterceptRule:
        return InterceptRule.model_validate(self.store.create_intercept_rule(payload))

    def list_rules(self, profile_id: int | None = None) -> list[InterceptRule]:
        return [InterceptRule.model_validate(row) for row in self.store.list_intercept_rules(profile_id)]

    def delete_rule(self, rule_id: str) -> bool:
        return self.store.delete_intercept_rule(rule_id)

    def _matching_decision(self, payload: HttpFlowCreate) -> InterceptDecision | None:
        for rule in self.list_rules(payload.profile_id):
            if not rule.enabled:
                continue
            if rule.method and rule.method.upper() != payload.method.upper():
                continue
            if not fnmatch(payload.host.lower(), rule.host_pattern.lower()):
                continue
            if not fnmatch(payload.path, rule.path_pattern):
                continue
            return rule.decision
        return None


def _host_allowed(host: str, allowed_hosts: list[str]) -> bool:
    normalized = host.lower().strip()
    for allowed in allowed_hosts:
        rule = allowed.lower().strip()
        if not rule:
            continue
        if normalized == rule:
            return True
        if rule.startswith("*.") and normalized.endswith(rule[1:]):
            return True
    return False


def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: "[redacted]" if key.lower() in SENSITIVE_HEADERS else value
        for key, value in headers.items()
    }
