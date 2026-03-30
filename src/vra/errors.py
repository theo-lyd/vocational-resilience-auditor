from __future__ import annotations


class PipelineError(Exception):
    """Base class for typed pipeline failures."""


class PipelineConfigurationError(PipelineError):
    """Raised when runtime pipeline configuration is invalid."""


class StageExecutionError(PipelineError):
    """Raised when a stage fails after retry attempts."""

    def __init__(self, stage_name: str, attempts: int, original_error: Exception):
        self.stage_name = stage_name
        self.attempts = attempts
        self.original_error = original_error
        message = (
            f"Stage '{stage_name}' failed after {attempts} attempts: "
            f"{type(original_error).__name__}: {original_error}"
        )
        super().__init__(message)


class OutputValidationError(PipelineError):
    """Raised when required pipeline outputs are missing or invalid."""


class ObservabilityWriteError(PipelineError):
    """Raised when observability artifacts cannot be persisted."""
