from pathlib import Path

from ..models import BrowserRuntimeStatus, Profile, SessionStatus
from .camoufox_launcher import CamoufoxLauncher
from .proxy_orchestrator import ProxyOrchestrator


class LauncherRegistry:
    def __init__(
        self,
        profiles_dir: Path | None = None,
        proxy_orchestrator: ProxyOrchestrator | None = None,
        camoufox_launcher: CamoufoxLauncher | None = None,
    ) -> None:
        self.profiles_dir = profiles_dir or Path(__file__).resolve().parents[2] / "profiles_data"
        self.proxy_orchestrator = proxy_orchestrator or ProxyOrchestrator()
        self.camoufox_launcher = camoufox_launcher or CamoufoxLauncher()
        self.sessions: dict[int, SessionStatus] = {}

    def launch(self, profile: Profile) -> SessionStatus:
        user_data_dir = self.profiles_dir / str(profile.id)
        user_data_dir.mkdir(parents=True, exist_ok=True)
        proxy = self.proxy_orchestrator.start(profile)
        options = self.camoufox_launcher.prepare_options(profile, proxy, user_data_dir)
        browser = self.camoufox_launcher.launch(profile, proxy, user_data_dir)
        status = SessionStatus(
            profile_id=profile.id,
            status=browser.status,
            browser_pid=browser.pid,
            proxy_port=proxy.port,
            user_data_dir=str(user_data_dir),
            runtime="camoufox",
            launch_options=_safe_launch_options(options),
            detail=f"{proxy.detail} {browser.detail}",
        )
        self.sessions[profile.id] = status
        return status

    def stop(self, profile_id: int) -> SessionStatus | None:
        previous = self.sessions.pop(profile_id, None)
        self.camoufox_launcher.stop(profile_id)
        self.proxy_orchestrator.stop(profile_id)
        if previous is None:
            return None
        return previous.model_copy(update={"status": "stopped", "detail": "Session removed from local registry."})

    def get(self, profile_id: int) -> SessionStatus | None:
        return self.sessions.get(profile_id)

    def get_browser(self, profile_id: int) -> BrowserRuntimeStatus | None:
        return self.camoufox_launcher.get(profile_id)


def _safe_launch_options(options: dict) -> dict:
    safe = dict(options)
    proxy = safe.get("proxy")
    if isinstance(proxy, dict) and "username" in proxy:
        safe["proxy"] = {**proxy, "username": "[redacted]"}
    return safe
