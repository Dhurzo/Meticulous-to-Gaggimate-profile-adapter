"""Espresso Profile Translator - Meticulous to Gaggimate conversion."""

__version__ = "0.1.0"

from .cli import app, main
from .translator import resolve_variables
from .exit_mode import convert_exit_triggers, detect_conflicting_triggers, ExitTarget

__all__ = ["__version__", "app", "main", "resolve_variables", "convert_exit_triggers", "detect_conflicting_triggers", "ExitTarget"]
