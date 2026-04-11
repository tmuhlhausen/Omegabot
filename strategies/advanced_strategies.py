"""DEPRECATED compatibility shim for advanced strategies.

Canonical path: ``src.strategies``.
This shim remains only for temporary backwards-compatibility and will be removed
per roadmap timeline.
"""

from warnings import warn

from src.strategies.import_map import *  # noqa: F401,F403

warn(
    "Importing from 'strategies.advanced_strategies' is deprecated; use "
    "'src.strategies.import_map' or 'src.strategies' instead.",
    DeprecationWarning,
    stacklevel=2,
)
