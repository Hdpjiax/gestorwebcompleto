from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status

from .models import (
    ActionStatus,
    AnonymityLevelUpdate,
    Flow,
    FlowReplayStatus,
    BrowserOpenRequest,
    BrowserOpenStatus,
    InterceptedRequest,
    Profile,
    ProfileCreate,
    ProfileUpdate,
    SessionStatus,
)
from .storage import SQLiteStore
from .services.anonymity_presets import list_presets
from .services.launcher import LauncherRegistry


app = FastAPI(
    title="Gestor Web Cybersecurity Backend",
    version="0.1.0",
    description="Initial API for educational and professional cybersecurity browser profiles.",
)

store: SQLiteStore | None = None
launcher = LauncherRegistry()

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


@app.get("/interceptor/requests", response_model=list[InterceptedRequest])
def list_interceptor_requests() -> list[InterceptedRequest]:
    return BUILTIN_REQUESTS


@app.post("/browser/open", response_model=BrowserOpenStatus)
def open_browser(payload: BrowserOpenRequest) -> BrowserOpenStatus:
    return BrowserOpenStatus(
        sessionId=f"stub-{payload.profileId}",
        status="stubbed",
        detail=f"Camoufox open is stubbed for {payload.url}; no browser process was started.",
    )


@app.websocket("/ws/flows/{profile_id}")
async def flows_websocket(websocket: WebSocket, profile_id: int) -> None:
    await websocket.accept()
    await websocket.send_json(
        {
            "type": "connected",
            "profile_id": profile_id,
            "message": "Flow event stream connected.",
        }
    )
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_json(
                {
                    "type": "echo",
                    "profile_id": profile_id,
                    "message": message,
                }
            )
    except WebSocketDisconnect:
        return
