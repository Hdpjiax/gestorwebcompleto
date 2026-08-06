import os
import shutil
import socket
import subprocess
from pathlib import Path

from ..models import Profile, ProxyStatus


class ProxyOrchestrator:
    def __init__(self, base_port: int = 9100, addon_path: Path | None = None) -> None:
        self.base_port = int(os.getenv("GESTOR_PROXY_BASE_PORT", str(base_port)))
        self.addon_path = addon_path or Path(__file__).resolve().parents[1] / "mitm_addons" / "capture_addon.py"
        self.processes: dict[int, subprocess.Popen] = {}
        self.statuses: dict[int, ProxyStatus] = {}

    def start(self, profile: Profile) -> ProxyStatus:
        existing = self.statuses.get(profile.id)
        if existing and existing.status in {"running", "stubbed"}:
            return existing

        port = self._reserve_port(profile.id)
        mitmdump = shutil.which("mitmdump")
        if mitmdump is None:
            status = ProxyStatus(
                profile_id=profile.id,
                status="stubbed",
                port=port,
                pid=None,
                addon_path=str(self.addon_path),
                detail="mitmdump not found; proxy runtime was not started.",
            )
            self.statuses[profile.id] = status
            return status

        command = [
            mitmdump,
            "--listen-host",
            "127.0.0.1",
            "--listen-port",
            str(port),
            "-s",
            str(self.addon_path),
        ]
        env = {
            **os.environ,
            "GESTOR_PROFILE_ID": str(profile.id),
            "GESTOR_BACKEND_URL": os.getenv("GESTOR_BACKEND_URL", "http://127.0.0.1:8756"),
        }
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        status = ProxyStatus(
            profile_id=profile.id,
            status="running",
            port=port,
            pid=process.pid,
            addon_path=str(self.addon_path),
            detail="mitmdump started on 127.0.0.1.",
        )
        self.processes[profile.id] = process
        self.statuses[profile.id] = status
        return status

    def stop(self, profile_id: int) -> ProxyStatus | None:
        previous = self.statuses.pop(profile_id, None)
        process = self.processes.pop(profile_id, None)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        if previous is None:
            return None
        return previous.model_copy(update={"status": "stopped", "pid": None, "detail": "Proxy process stopped or stub cleared."})

    def get(self, profile_id: int) -> ProxyStatus | None:
        status = self.statuses.get(profile_id)
        process = self.processes.get(profile_id)
        if status and process and process.poll() is not None:
            return status.model_copy(update={"status": "error", "detail": "mitmdump exited unexpectedly."})
        return status

    def _reserve_port(self, profile_id: int) -> int:
        preferred = self.base_port + profile_id
        for port in range(preferred, preferred + 100):
            if self._is_available(port):
                return port
        raise RuntimeError("No local proxy port available")

    @staticmethod
    def _is_available(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            return sock.connect_ex(("127.0.0.1", port)) != 0
