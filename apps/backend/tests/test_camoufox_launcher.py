from datetime import datetime, timezone
from pathlib import Path

from app.models import AnonymityLevel, Profile, ProxyStatus
from app.services.camoufox_launcher import CamoufoxLauncher


def test_camoufox_launcher_prepares_options_and_stubs_without_package(tmp_path: Path) -> None:
    profile = Profile(
        id=7,
        name="Camoufox Test",
        description=None,
        anonymity_level=AnonymityLevel.high,
        proxy=None,
        camoufox_config={"headless": True},
        is_running=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    proxy = ProxyStatus(profile_id=7, status="stubbed", port=9107, detail="proxy stubbed")
    launcher = CamoufoxLauncher()

    options = launcher.prepare_options(profile, proxy, tmp_path)
    status = launcher.launch(profile, proxy, tmp_path)

    assert options["user_data_dir"] == str(tmp_path)
    assert options["proxy"]["server"] == "http://127.0.0.1:9107"
    assert status.status in {"stubbed", "prepared"}
    assert launcher.get(profile.id) == status
    assert launcher.stop(profile.id).status == "stopped"
