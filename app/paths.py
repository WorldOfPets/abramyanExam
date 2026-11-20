"""Paths that work both from source and inside a PyInstaller one-file bundle."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_root() -> Path:
    """Return the root that contains the ``app`` package resources."""
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle)
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)
