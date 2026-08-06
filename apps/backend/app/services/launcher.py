from pathlib import Path

from ..models import Profile, SessionStatus
from .anonymity_presets import build_camoufox_config


class LauncherRegistry:
    def __init__(self, profiles_dir: Path | None = None) -> None:
        self.profiles_dir = profiles_dir or Path(__file__).resolve().parents[2] / "profiles_data"
        self.sessions: dict[int, SessionStatus] = {}

    def launch(self, profile: Profile) -> SessionStatus:
        user_data_dir = self.profiles_dir / str(profile.id)
        user_data_dir.mkdir(parents=True, exist_ok=True)
        config = build_camoufox_config(profile)
        status = SessionStatus(
            profile_id=profile.id,
            status="stubbed",
            browser_pid=None,
            proxy_port=9000 + profile.id,
            user_data_dir=str(user_data_dir),
            detail=f"Prepared Camoufox config keys: {', '.join(sorted(config.keys()))}. Runtime launch is stubbed.",
        )
        self.sessions[profile.id] = status
        return status

    def stop(self, profile_id: int) -> SessionStatus | None:
        previous = self.sessions.pop(profile_id, None)
        if previous is None:
            return None
        return previous.model_copy(update={"status": "stopped", "detail": "Session removed from local registry."})

    def get(self, profile_id: int) -> SessionStatus | None:
        return self.sessions.get(profile_id)
