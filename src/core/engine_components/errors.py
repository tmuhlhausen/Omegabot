from __future__ import annotations


class EngineLoopError(Exception):
    """Base class for recoverable loop failures."""


class PriceFeedProcessingError(EngineLoopError):
    """Raised when a market tick cannot be processed."""


class ScalingEvaluationError(EngineLoopError):
    """Raised when scaling evaluation fails."""


class HudSyncError(EngineLoopError):
    """Raised when HUD synchronization fails."""


class NonceResyncError(EngineLoopError):
    """Raised when nonce resync fails."""


class HealthUpdateError(EngineLoopError):
    """Raised when health telemetry update fails."""
