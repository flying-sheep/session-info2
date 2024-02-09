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

data_dir = Path(__file__).parent / "data"


@pytest.fixture()
def import_path(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Callable[[str], Any], None, None]:
    monkeypatch.setattr("sys.path", [str(data_dir)])
    sm = sys.modules.copy()

    def import_path(path: str) -> Any:  # noqa: ANN401
        assert (m := re.fullmatch(r"([\w.]+)(?::(\w+))?", path))
        module_name, member_name = m.groups()

        mod = importlib.import_module(module_name)
        if member_name:
            return getattr(mod, member_name)
        return mod

    yield import_path

    sys.modules = sm
