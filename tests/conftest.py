# SPDX-License-Identifier: MPL-2.0
"""Test utils/setup."""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def libdir_test(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Prepend the data dir to sys.path and mark sys.modules for restoring."""
    monkeypatch.syspath_prepend(str(DATA_DIR))
    return DATA_DIR


@pytest.fixture
def import_path(libdir_test: Path) -> Generator[Callable[[str], Any], None, None]:
    del libdir_test  # used for side effects
    added_modules: set[str] = set()

    def import_path(path: str) -> Any:  # noqa: ANN401
        nonlocal added_modules

        assert (m := re.fullmatch(r"([\w.]+)(?::(\w+))?", path))
        module_name, member_name = m.groups()

        sm_before = set(sys.modules)
        mod = importlib.import_module(module_name)
        sm_after = set(sys.modules)

        added_modules |= sm_after - sm_before
        if member_name:
            return getattr(mod, member_name)
        return mod

    yield import_path

    for m in added_modules:
        del sys.modules[m]
