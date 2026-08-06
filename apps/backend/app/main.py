from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status

from .models import (
    ActionStatus,
    AnonymityLevelUpdate,
    Flow,
    FlowDecision,
    FlowDecisionRequest,
    FlowReplayStatus,
    BrowserOpenRequest,
    BrowserOpenStatus,
    BrowserRuntimeStatus,
    HttpFlow,
    HttpFlowCreate,
    InterceptedRequest,
    InterceptRule,
    InterceptRuleCreate,
    Profile,
    ProfileCreate,
    ProfileUpdate,
    ProxyStatus,
    ReplayRequest,
    SessionStatus,
)
from .storage import SQLiteStore
from .services.anonymity_presets import list_presets
from .services.interceptor import InterceptorService
from .services.launcher import LauncherRegistry
from .services.realtime import RealtimeHub


app = FastAPI(
    title="Gestor Web Cybersecurity Backend",
    version="0.1.0",
    description="Initial API for educational and professional cybersecurity browser profiles.",
)

store: SQLiteStore | None = None
launcher = LauncherRegistry()
realtime = RealtimeHub()

BUILTIN_FLOWS = [
    Flow(
        id="baseline-recon",
        name="Baseline Recon",
        description="Safe placeholder flow for supervised reconnaissance training.",
        steps=["open_target", "capture_metadata", "summarize_findings"],
    ),
    Flow(
        id="privacy-check",
        name="Privacy Check",
        description="Safe placeholder flow for validating profile privacy settings.",
        steps=["launch_profile", "inspect_fingerprint", "record_result"],
    ),
]

BUILTIN_REQUESTS = [
    InterceptedRequest(
        id="req-baseline-1",
        method="GET",
        host="training.portal.local",
        path="/login",
        status=200,
        type="document",
        profile="Baseline Recon",
        time="09:12:18",
    ),
    InterceptedRequest(
        id="req-baseline-2",
        method="POST",
        host="training.portal.local",
        path="/api/session",
        status=403,
        type="xhr",
        profile="Baseline Recon",
        time="09:12:26",
    ),
]


def get_store() -> Generator[SQLiteStore, None, None]:
    global store
    if store is None:
        store = SQLiteStore()
    yield store


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/profiles", response_model=list[Profile])
def list_profiles(db: SQLiteStore = Depends(get_store)) -> list[dict]:
    return db.list_profiles()


@app.post("/profiles", response_model=Profile, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, db: SQLiteStore = Depends(get_store)) -> dict:
    return db.create_profile(payload)


@app.get("/profiles/{profile_id}", response_model=Profile)
def get_profile(profile_id: int, db: SQLiteStore = Depends(get_store)) -> dict:
    profile = db.get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@app.put("/profiles/{profile_id}", response_model=Profile)
def update_profile(profile_id: int, payload: ProfileUpdate, db: SQLiteStore = Depends(get_store)) -> dict:
    profile = db.update_profile(profile_id, payload)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@app.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: int, db: SQLiteStore = Depends(get_store)) -> None:
    if not db.delete_profile(profile_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")


@app.post("/profiles/{profile_id}/launch", response_model=SessionStatus)
def launch_profile(profile_id: int, db: SQLiteStore = Depends(get_store)) -> SessionStatus:
    existing = db.get_profile(profile_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    profile = Profile.model_validate(existing)
    session = launcher.launch(profile)
    db.set_running(profile_id, True)
    return session


@app.post("/profiles/{profile_id}/stop", response_model=SessionStatus)
def stop_profile(profile_id: int, db: SQLiteStore = Depends(get_store)) -> SessionStatus:
    profile = db.set_running(profile_id, False)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return launcher.stop(profile_id) or SessionStatus(
        profile_id=profile_id,
        status="stopped",
        browser_pid=None,
        proxy_port=None,
        user_data_dir=str(launcher.profiles_dir / str(profile_id)),
        detail="No active runtime session was registered.",
    )


@app.get("/profiles/{profile_id}/session", response_model=SessionStatus | None)
def get_profile_session(profile_id: int) -> SessionStatus | None:
    return launcher.get(profile_id)


@app.get("/profiles/{profile_id}/proxy", response_model=ProxyStatus | None)
def get_profile_proxy(profile_id: int) -> ProxyStatus | None:
    return launcher.proxy_orchestrator.get(profile_id)


@app.get("/profiles/{profile_id}/browser", response_model=BrowserRuntimeStatus | None)
def get_profile_browser(profile_id: int) -> BrowserRuntimeStatus | None:
    return launcher.get_browser(profile_id)


@app.put("/profiles/{profile_id}/anonymity-level", response_model=Profile)
def set_anonymity_level(
    profile_id: int,
    payload: AnonymityLevelUpdate,
    db: SQLiteStore = Depends(get_store),
) -> dict:
    profile = db.set_anonymity_level(profile_id, payload.anonymity_level)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@app.get("/anonymity/presets")
def get_anonymity_presets() -> list:
    return list_presets()


@app.get("/flows", response_model=list[Flow])
def list_flows() -> list[Flow]:
    return BUILTIN_FLOWS


@app.post("/flows/{flow_id}/replay", response_model=FlowReplayStatus)
def replay_flow(flow_id: str) -> FlowReplayStatus:
    if flow_id not in {flow.id for flow in BUILTIN_FLOWS}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    return FlowReplayStatus(
        flow_id=flow_id,
        status="stubbed",
        detail="Flow replay is intentionally stubbed; no browser automation was executed.",
    )


@app.get("/interceptor/flows", response_model=list[HttpFlow])
def list_http_flows(profile_id: int | None = None, db: SQLiteStore = Depends(get_store)) -> list[HttpFlow]:
    return InterceptorService(db).list_flows(profile_id)


@app.post("/interceptor/flows", response_model=HttpFlow, status_code=status.HTTP_201_CREATED)
async def record_http_flow(payload: HttpFlowCreate, db: SQLiteStore = Depends(get_store)) -> HttpFlow:
    if db.get_profile(payload.profile_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    flow = InterceptorService(db).record_flow(payload)
    await realtime.broadcast(payload.profile_id, "flow.created", flow.model_dump(mode="json"))
    return flow


@app.get("/interceptor/requests", response_model=list[InterceptedRequest])
def list_interceptor_requests(profile_id: int | None = None, db: SQLiteStore = Depends(get_store)) -> list[InterceptedRequest]:
    rows = InterceptorService(db).list_request_rows(profile_id)
    return rows or BUILTIN_REQUESTS


@app.post("/interceptor/flows/{flow_id}/replay", response_model=FlowReplayStatus)
def replay_http_flow(
    flow_id: str,
    payload: ReplayRequest | None = None,
    db: SQLiteStore = Depends(get_store),
) -> FlowReplayStatus:
    result = InterceptorService(db).replay(flow_id, payload)
    if result["status"] == "missing":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["detail"])
    return FlowReplayStatus(flow_id=flow_id, status=result["status"], detail=result["detail"])


@app.post("/interceptor/flows/{flow_id}/decision", response_model=FlowDecision)
async def decide_http_flow(
    flow_id: str,
    payload: FlowDecisionRequest,
    db: SQLiteStore = Depends(get_store),
) -> FlowDecision:
    service = InterceptorService(db)
    decision = service.decide(flow_id, payload)
    if decision is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    flow = db.get_http_flow(flow_id)
    if flow is not None:
        await realtime.broadcast(flow["profile_id"], "flow.decision", decision.model_dump(mode="json"))
    return decision


@app.get("/interceptor/flows/{flow_id}/decisions", response_model=list[FlowDecision])
def list_http_flow_decisions(flow_id: str, db: SQLiteStore = Depends(get_store)) -> list[FlowDecision]:
    if db.get_http_flow(flow_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    return InterceptorService(db).list_decisions(flow_id)


@app.get("/interceptor/rules", response_model=list[InterceptRule])
def list_intercept_rules(profile_id: int | None = None, db: SQLiteStore = Depends(get_store)) -> list[InterceptRule]:
    return InterceptorService(db).list_rules(profile_id)


@app.post("/interceptor/rules", response_model=InterceptRule, status_code=status.HTTP_201_CREATED)
def create_intercept_rule(payload: InterceptRuleCreate, db: SQLiteStore = Depends(get_store)) -> InterceptRule:
    if db.get_profile(payload.profile_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return InterceptorService(db).create_rule(payload)


@app.delete("/interceptor/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_intercept_rule(rule_id: str, db: SQLiteStore = Depends(get_store)) -> None:
    if not InterceptorService(db).delete_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")


@app.post("/browser/open", response_model=BrowserOpenStatus)
def open_browser(payload: BrowserOpenRequest) -> BrowserOpenStatus:
    return BrowserOpenStatus(
        sessionId=f"stub-{payload.profileId}",
        status="stubbed",
        detail=f"Camoufox open is stubbed for {payload.url}; no browser process was started.",
    )


@app.websocket("/ws/flows/{profile_id}")
async def flows_websocket(websocket: WebSocket, profile_id: int) -> None:
    await realtime.connect(profile_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime.disconnect(profile_id, websocket)
        return
