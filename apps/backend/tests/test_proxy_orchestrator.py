from datetime import datetime, timezone
from pathlib import Path

from app.models import AnonymityLevel, Profile
from app.services.proxy_orchestrator import ProxyOrchestrator


def test_proxy_orchestrator_stubs_when_mitmdump_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("app.services.proxy_orchestrator.shutil.which", lambda _: None)
    profile = Profile(
        id=42,
        name="Proxy Test",
        description=None,
        anonymity_level=AnonymityLevel.medium,
        proxy=None,
        camoufox_config={},
        is_running=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    orchestrator = ProxyOrchestrator(base_port=9500, addon_path=tmp_path / "capture_addon.py")

    status = orchestrator.start(profile)

    assert status.status == "stubbed"
    assert status.port >= 9542
    assert "mitmdump not found" in status.detail
    assert orchestrator.get(profile.id) == status
    assert orchestrator.stop(profile.id).status == "stopped"
