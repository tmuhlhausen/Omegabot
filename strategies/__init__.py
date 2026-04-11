"""DEPRECATED compatibility shim package.

Canonical path: ``src.strategies``.
"""

from warnings import warn

warn(
    "Package 'strategies' is deprecated; import from 'src.strategies' instead.",
    DeprecationWarning,
    stacklevel=2,
)
