"""Profile validation module - compares Meticulous and Gaggimate extraction profiles."""

__version__ = "0.1.0"

from .cli import app, main
from .core import (
    TOLERANCES,
    detect_gaggimate_phase_type,
    detect_meticulous_phase_type,
    validate_batch,
    validate_phase_types,
    validate_profile_pair,
    verify_phase_ordering,
)
from .models import (
    BatchValidationResult,
    GaggimatePhaseData,
    MeticulousStageData,
    PhaseDeviation,
    PhaseMatch,
    PhaseType,
    PhaseTypeResult,
    PhaseTypeValidationReport,
    ProfileValidationResult,
    StagePoint,
    ValidationResult,
)
from .reporter import ProfileResult, generate_report

__all__ = [
    "__version__",
    "app",
    "main",
    "TOLERANCES",
    "validate_batch",
    "validate_profile_pair",
    "validate_phase_types",
    "detect_meticulous_phase_type",
    "detect_gaggimate_phase_type",
    "verify_phase_ordering",
    "BatchValidationResult",
    "GaggimatePhaseData",
    "MeticulousStageData",
    "PhaseDeviation",
    "PhaseMatch",
    "PhaseType",
    "PhaseTypeResult",
    "PhaseTypeValidationReport",
    "ProfileValidationResult",
    "ProfileResult",
    "StagePoint",
    "ValidationResult",
    "generate_report",
]
