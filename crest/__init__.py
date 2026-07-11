"""crest — generative terminal-art CLI.

Public surface so callers can ``import crest`` and reach the core helpers
without digging into submodules.
"""

from __future__ import annotations

from . import colors, patterns, render

__version__ = "0.1.0"

__all__ = ["colors", "patterns", "render", "__version__"]
