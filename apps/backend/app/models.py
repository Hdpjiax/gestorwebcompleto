from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnonymityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ProxyScheme(str, Enum):
    http = "http"
    https = "https"
    socks5 = "socks5"


class ProxyConfig(BaseModel):
    scheme: ProxyScheme = ProxyScheme.http
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str | None = Field(default=None, max_length=255)


class ProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    anonymity_level: AnonymityLevel = AnonymityLevel.medium
    proxy: ProxyConfig | None = None
    camoufox_config: dict[str, Any] = Field(default_factory=dict)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    anonymity_level: AnonymityLevel | None = None
    proxy: ProxyConfig | None = None
    camoufox_config: dict[str, Any] | None = None


class Profile(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_running: bool = False
    created_at: datetime
    updated_at: datetime


class AnonymityLevelUpdate(BaseModel):
    anonymity_level: AnonymityLevel


class ActionStatus(BaseModel):
    profile_id: int
    status: str
    detail: str


class SessionStatus(BaseModel):
    profile_id: int
    status: str
    browser_pid: int | None = None
    proxy_port: int | None = None
    user_data_dir: str
    detail: str


class AnonymityPreset(BaseModel):
    level: AnonymityLevel
    label: str
    requires_proxy: bool
    camoufox_options: dict[str, Any]
    firefox_prefs: dict[str, Any]
    notes: list[str]


class Flow(BaseModel):
    id: str
    name: str
    description: str | None = None
    steps: list[str] = Field(default_factory=list)


class FlowReplayStatus(BaseModel):
    flow_id: str
    status: str
    detail: str


class HttpFlowCreate(BaseModel):
    profile_id: int
    method: str = Field(min_length=1, max_length=12)
    scheme: str = Field(default="https", max_length=12)
    host: str = Field(min_length=1, max_length=255)
    path: str = Field(default="/", max_length=2048)
    status_code: int | None = Field(default=None, ge=100, le=599)
    request_headers: dict[str, str] = Field(default_factory=dict)
    response_headers: dict[str, str] = Field(default_factory=dict)
    request_body_preview: str | None = Field(default=None, max_length=4096)
    response_body_preview: str | None = Field(default=None, max_length=4096)
    resource_type: str = Field(default="xhr", max_length=32)
    in_scope: bool = True


class HttpFlow(HttpFlowCreate):
    id: str
    captured_at: datetime
    replayable: bool = True
    intercept_decision: str = "forward"


class ReplayRequest(BaseModel):
    method: str | None = Field(default=None, max_length=12)
    path: str | None = Field(default=None, max_length=2048)
    headers: dict[str, str] | None = None
    body_preview: str | None = Field(default=None, max_length=4096)


class InterceptedRequest(BaseModel):
    id: str
    method: str
    host: str
    path: str
    status: int
    type: str
    profile: str
    time: str


class BrowserOpenRequest(BaseModel):
    profileId: str
    url: str


class BrowserOpenStatus(BaseModel):
    sessionId: str
    status: str
    detail: str
