"""Backward-compatible transition imports for early Novel OS prototypes."""
from .delta import apply_operations, propose_delta, validate_delta_paths

__all__ = ["apply_operations", "propose_delta", "validate_delta_paths"]
