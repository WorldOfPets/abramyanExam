"""``python -m app`` entry point."""

from __future__ import annotations

import multiprocessing

from app.main import run

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
