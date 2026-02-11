"""Custom exceptions for profile validation."""

from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    """Base exception for profile validation errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class ProfileLoadError(ValidationError):
    """Failed to load a profile file."""

    pass


class PhaseMismatchError(ValidationError):
    """Phase count or structure mismatch between profiles."""

    pass


class ToleranceExceededError(ValidationError):
    """A value exceeded the acceptable tolerance."""

    def __init__(
        self,
        variable: str,
        meticulous_value: float,
        gaggimate_value: float,
        tolerance: float,
        percentage_tolerance: float,
        actual_difference: float,
        percentage_difference: float,
    ) -> None:
        self.variable = variable
        self.meticulous_value = meticulous_value
        self.gaggimate_value = gaggimate_value
        self.tolerance = tolerance
        self.percentage_tolerance = percentage_tolerance
        self.actual_difference = actual_difference
        self.percentage_difference = percentage_difference
        message = (
            f"{variable} tolerance exceeded: "
            f"Meticulous={meticulous_value}, Gaggimate={gaggimate_value}, "
            f"Diff={actual_difference:.3f} ({percentage_difference:.1f}%), "
            f"Tolerance={tolerance} ({percentage_tolerance}%)"
        )
        details = (
            f"Meticulous value: {meticulous_value}\n"
            f"Gaggimate value: {gaggimate_value}\n"
            f"Absolute difference: {actual_difference:.3f}\n"
            f"Percentage difference: {percentage_difference:.1f}%\n"
            f"Absolute tolerance: {tolerance}\n"
            f"Percentage tolerance: {percentage_tolerance}%"
        )
        super().__init__(message, details)
