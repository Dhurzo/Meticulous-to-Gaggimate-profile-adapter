"""Data models for profile validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel


@dataclass
class StagePoint:
    """A single point in a Meticulous stage dynamics curve."""

    time: float
    value: float


@dataclass
class MeticulousStageData:
    """Extracted data from a Meticulous stage for validation."""

    name: str
    key: str
    stage_type: Literal["flow", "pressure", "power"]
    points: list[StagePoint]
    duration: float
    controlled_variable: Literal["flow", "pressure"]


@dataclass
class GaggimatePhaseData:
    """Extracted data from a Gaggimate phase for validation."""

    name: str
    phase_type: str
    duration: float
    pressure: float | None = None
    flow: float | None = None


@dataclass
class PhaseMatch:
    """Represents a matched pair of Meticulous stage and Gaggimate phase."""

    meticulous_stage: MeticulousStageData
    gaggimate_phase: GaggimatePhaseData
    split_index: int | None = None
    total_splits: int | None = None


@dataclass
class PhaseDeviation:
    """A deviation found during phase validation."""

    phase_name: str
    variable: str
    meticulous_value: float
    gaggimate_value: float
    deviation_absolute: float
    deviation_percentage: float
    within_tolerance: bool
    tolerance_used: str
    tolerance_value: float


@dataclass
class ValidationResult:
    """Result of validating a single phase match."""

    phase_match: PhaseMatch
    deviations: list[PhaseDeviation] = field(default_factory=list)
    passed: bool = True
    error_message: str | None = None


@dataclass
class ProfileValidationResult:
    """Complete validation result for a profile pair."""

    profile_name: str
    meticulous_file: Path
    gaggimate_file: Path
    phase_results: list[ValidationResult] = field(default_factory=list)
    total_phases: int = 0
    passed_phases: int = 0
    failed_phases: int = 0
    total_deviations: int = 0
    passed: bool = True
    error_message: str | None = None

    def summary(self) -> str:
        """Generate a summary of the validation result."""
        lines = [
            f"Profile: {self.profile_name}",
            f"Phases: {self.passed_phases}/{self.total_phases} passed",
            f"Deviations: {self.total_deviations}",
        ]
        if self.failed_phases > 0:
            lines.append(f"\nFailed phases:")
            for result in self.phase_results:
                if not result.passed:
                    lines.append(f"  - {result.phase_match.meticulous_stage.name}: {result.error_message}")
        return "\n".join(lines)


@dataclass
class BatchValidationResult:
    """Result of batch validation across multiple profiles."""

    total_profiles: int = 0
    passed_profiles: int = 0
    failed_profiles: int = 0
    profile_results: list[ProfileValidationResult] = field(default_factory=list)

    def summary(self) -> str:
        """Generate a summary of batch validation."""
        lines = [
            f"Batch Validation Summary",
            f"Profiles: {self.passed_profiles}/{self.total_profiles} passed",
            f"Failed: {self.failed_profiles}",
        ]
        if self.profile_results:
            lines.append("\nProfile Results:")
            for result in self.profile_results:
                status = "✓" if result.passed else "✗"
                lines.append(
                    f"  {status} {result.profile_name}: "
                    f"{result.passed_phases}/{result.total_phases} phases, "
                    f"{result.total_deviations} deviations"
                )
        return "\n".join(lines)


class PhaseType(str, Enum):
    PREINFUSION = "preinfusion"
    BREW = "brew"
    UNKNOWN = "unknown"


class PhaseTypeResult(BaseModel):
    stage_key: str
    original_type: PhaseType
    translated_type: PhaseType
    matched: bool
    expected_type: Optional[PhaseType] = None


class PhaseTypeValidationReport(BaseModel):
    profile_name: str
    original_path: Path
    translated_path: Path
    phases_checked: int
    type_mismatches: list[PhaseTypeResult]
    ordering_correct: bool
    overall_passed: bool
    summary: str
