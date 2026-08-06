from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnonymityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    anonymity_level: AnonymityLevel = AnonymityLevel.medium
    camoufox_config: dict[str, Any] = Field(default_factory=dict)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    anonymity_level: AnonymityLevel | None = None
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


class Flow(BaseModel):
    id: str
    name: str
    description: str | None = None
    steps: list[str] = Field(default_factory=list)


class FlowReplayStatus(BaseModel):
    flow_id: str
    status: str
    detail: str


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
