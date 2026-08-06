from pathlib import Path
from typing import Any

from ..models import BrowserRuntimeStatus, Profile, ProxyStatus
from .anonymity_presets import build_camoufox_config


class CamoufoxLauncher:
    def __init__(self) -> None:
        self.runtimes: dict[int, BrowserRuntimeStatus] = {}

    def prepare_options(self, profile: Profile, proxy: ProxyStatus, user_data_dir: Path) -> dict[str, Any]:
        options = build_camoufox_config(profile)
        options["user_data_dir"] = str(user_data_dir)
        options["proxy"] = {"server": f"http://127.0.0.1:{proxy.port}"}
        return options

    def launch(self, profile: Profile, proxy: ProxyStatus, user_data_dir: Path) -> BrowserRuntimeStatus:
        options = self.prepare_options(profile, proxy, user_data_dir)
        if proxy.status not in {"running", "stubbed"}:
            status = BrowserRuntimeStatus(
                profile_id=profile.id,
                status="blocked",
                pid=None,
                detail=f"Proxy is not ready: {proxy.status}",
            )
            self.runtimes[profile.id] = status
            return status

        try:
            import camoufox  # noqa: F401
        except ImportError:
            status = BrowserRuntimeStatus(
                profile_id=profile.id,
                status="stubbed",
                pid=None,
                detail=f"Camoufox package not installed; prepared {len(options)} launch option(s).",
            )
            self.runtimes[profile.id] = status
            return status

        status = BrowserRuntimeStatus(
            profile_id=profile.id,
            status="prepared",
            pid=None,
            detail="Camoufox package detected; async browser startup is queued for the next runtime milestone.",
        )
        self.runtimes[profile.id] = status
        return status

    def stop(self, profile_id: int) -> BrowserRuntimeStatus | None:
        previous = self.runtimes.pop(profile_id, None)
        if previous is None:
            return None
        return previous.model_copy(update={"status": "stopped", "pid": None, "detail": "Browser runtime cleared."})

    def get(self, profile_id: int) -> BrowserRuntimeStatus | None:
        return self.runtimes.get(profile_id)
