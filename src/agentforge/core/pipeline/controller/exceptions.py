"""
Pipeline Exceptions
===================

Exception classes for pipeline operations.
"""


class PipelineError(Exception):
    """Base exception for pipeline errors."""

    pass


class PipelineNotFoundError(PipelineError):
    """Raised when a pipeline is not found."""

    pass


class PipelineStateError(PipelineError):
    """Raised when pipeline is in invalid state for operation."""

    pass
