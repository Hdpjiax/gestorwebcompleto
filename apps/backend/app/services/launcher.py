from pathlib import Path

from ..models import Profile, SessionStatus
from .anonymity_presets import build_camoufox_config
from .proxy_orchestrator import ProxyOrchestrator


class LauncherRegistry:
    def __init__(self, profiles_dir: Path | None = None, proxy_orchestrator: ProxyOrchestrator | None = None) -> None:
        self.profiles_dir = profiles_dir or Path(__file__).resolve().parents[2] / "profiles_data"
        self.proxy_orchestrator = proxy_orchestrator or ProxyOrchestrator()
        self.sessions: dict[int, SessionStatus] = {}

    def launch(self, profile: Profile) -> SessionStatus:
        user_data_dir = self.profiles_dir / str(profile.id)
        user_data_dir.mkdir(parents=True, exist_ok=True)
        config = build_camoufox_config(profile)
        proxy = self.proxy_orchestrator.start(profile)
        status = SessionStatus(
            profile_id=profile.id,
            status="stubbed" if proxy.status == "stubbed" else "prepared",
            browser_pid=None,
            proxy_port=proxy.port,
            user_data_dir=str(user_data_dir),
            detail=f"{proxy.detail} Prepared Camoufox config keys: {', '.join(sorted(config.keys()))}. Browser launch is stubbed.",
        )
        self.sessions[profile.id] = status
        return status

    def stop(self, profile_id: int) -> SessionStatus | None:
        previous = self.sessions.pop(profile_id, None)
        self.proxy_orchestrator.stop(profile_id)
        if previous is None:
            return None
        return previous.model_copy(update={"status": "stopped", "detail": "Session removed from local registry."})

    def get(self, profile_id: int) -> SessionStatus | None:
        return self.sessions.get(profile_id)
