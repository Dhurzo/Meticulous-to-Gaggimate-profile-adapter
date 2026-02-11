from typing import Literal

from pydantic import BaseModel


class Variable(BaseModel):
    name: str
    key: str
    type: str
    value: float


class Dynamics(BaseModel):
    points: list[list[float | int]]
    over: str
    interpolation: str


class ExitTrigger(BaseModel):
    type: str
    value: float
    relative: bool
    comparison: str


class Stage(BaseModel):
    name: str
    key: str
    type: Literal["power", "flow", "pressure"]  # Validated at parse time
    dynamics: Dynamics
    exit_triggers: list[ExitTrigger]
    limits: list[dict] = []


class Author(BaseModel):
    name: str
    author_id: str
    profile_id: str | None = None


class MeticulousProfile(BaseModel):
    name: str
    id: str
    author: str
    author_id: str
    previous_authors: list[Author] = []
    temperature: float
    final_weight: float
    variables: list[Variable] = []
    stages: list[Stage]
