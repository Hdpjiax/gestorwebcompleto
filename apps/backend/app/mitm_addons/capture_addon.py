import json
import os
import urllib.error
import urllib.request

from mitmproxy import http


BACKEND_URL = os.getenv("GESTOR_BACKEND_URL", "http://127.0.0.1:8756").rstrip("/")
PROFILE_ID = int(os.getenv("GESTOR_PROFILE_ID", "0"))
MAX_BODY_PREVIEW = int(os.getenv("GESTOR_FLOW_BODY_PREVIEW", "2048"))


def response(flow: http.HTTPFlow) -> None:
    if PROFILE_ID <= 0:
        return

    payload = {
        "profile_id": PROFILE_ID,
        "method": flow.request.method,
        "scheme": flow.request.scheme,
        "host": flow.request.host,
        "path": flow.request.path or "/",
        "status_code": flow.response.status_code if flow.response else None,
        "request_headers": dict(flow.request.headers),
        "response_headers": dict(flow.response.headers) if flow.response else {},
        "request_body_preview": _preview(flow.request.raw_content),
        "response_body_preview": _preview(flow.response.raw_content if flow.response else None),
        "resource_type": _resource_type(flow),
        "in_scope": True,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BACKEND_URL}/interceptor/flows",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=2).read()
    except (urllib.error.URLError, TimeoutError):
        return


def _preview(content: bytes | None) -> str | None:
    if not content:
        return None
    return content[:MAX_BODY_PREVIEW].decode("utf-8", errors="replace")


def _resource_type(flow: http.HTTPFlow) -> str:
    accept = flow.request.headers.get("accept", "")
    content_type = flow.response.headers.get("content-type", "") if flow.response else ""
    value = f"{accept} {content_type}".lower()
    if "text/html" in value:
        return "document"
    if "javascript" in value:
        return "script"
    if "image/" in value:
        return "image"
    if "text/css" in value:
        return "style"
    return "xhr"
