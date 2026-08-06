from typing import Any

from ..models import AnonymityLevel, AnonymityPreset, Profile


PRESETS: dict[AnonymityLevel, AnonymityPreset] = {
    AnonymityLevel.low: AnonymityPreset(
        level=AnonymityLevel.low,
        label="Basico",
        requires_proxy=False,
        camoufox_options={"geoip": False, "block_webrtc": False},
        firefox_prefs={"privacy.resistFingerprinting": False},
        notes=["Fingerprint por perfil", "Proxy opcional", "Cookies aisladas por user_data_dir"],
    ),
    AnonymityLevel.medium: AnonymityPreset(
        level=AnonymityLevel.medium,
        label="Medio",
        requires_proxy=True,
        camoufox_options={"geoip": True, "block_webrtc": True},
        firefox_prefs={"media.peerconnection.enabled": False},
        notes=["Alinea timezone/geolocalizacion con proxy", "Bloquea WebRTC", "Headers consistentes"],
    ),
    AnonymityLevel.high: AnonymityPreset(
        level=AnonymityLevel.high,
        label="Maximo",
        requires_proxy=True,
        camoufox_options={
            "geoip": True,
            "block_webrtc": True,
            "viewport": {"width": 1280, "height": 720},
        },
        firefox_prefs={
            "privacy.resistFingerprinting": True,
            "webgl.disabled": True,
            "browser.cache.disk.enable": False,
        },
        notes=["Fingerprint uniforme", "WebGL/Canvas reducidos", "Cache deshabilitada"],
    ),
}


def list_presets() -> list[AnonymityPreset]:
    return list(PRESETS.values())


def build_camoufox_config(profile: Profile) -> dict[str, Any]:
    preset = PRESETS[profile.anonymity_level]
    merged = {
        "persistent_context": True,
        "config": {
            "firefox_user_prefs": preset.firefox_prefs,
            **profile.camoufox_config,
        },
        **preset.camoufox_options,
    }

    if profile.proxy is not None:
        merged["proxy"] = {
            "server": f"{profile.proxy.scheme.value}://{profile.proxy.host}:{profile.proxy.port}",
            **({"username": profile.proxy.username} if profile.proxy.username else {}),
        }

    return merged
