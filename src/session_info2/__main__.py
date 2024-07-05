"""CLI."""

from __future__ import annotations

from . import session_info

print(session_info(cpu=True, dependencies=True))
