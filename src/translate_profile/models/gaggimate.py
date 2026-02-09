from typing import Annotated

from pydantic import BaseModel, Field


class TransitionSettings(BaseModel):
    type: str
    duration: Annotated[float, Field(ge=0)]
    adaptive: bool


class ExitTarget(BaseModel):
    type: str
    operator: str
    value: float


class PumpSettings(BaseModel):
    target: str
    pressure: Annotated[float, Field(ge=0, le=15)]
    flow: Annotated[float, Field(ge=0)]


class GaggimatePhase(BaseModel):
    name: str
    phase: str
    valve: int
    duration: Annotated[float, Field(gt=0)]
    temperature: Annotated[float, Field(ge=0, le=150)]
    transition: TransitionSettings
    pump: PumpSettings | int
    targets: list[ExitTarget]


class GaggimateProfile(BaseModel):
    label: str
    type: str
    description: str | None = None
    temperature: Annotated[float, Field(ge=0, le=150)]
    utility: bool
    phases: list[GaggimatePhase]
