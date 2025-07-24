# SPDX-License-Identifier: MPL-2.0
"""Test helper utils."""

from __future__ import annotations

from importlib.metadata import PathDistribution
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from session_info2 import _mods
from session_info2._dists import _top_level_editable

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("mod_name", "expected"),
    [
        pytest.param("foo", ["foo"], id="one"),
        pytest.param("foo.bar", ["foo.bar", "foo"], id="two"),
        pytest.param("foo.bar.baz", ["foo.bar.baz", "foo.bar", "foo"], id="three"),
    ],
)
def test_mods(mod_name: str, expected: list[str]) -> None:
    assert list(_mods(mod_name)) == expected


def test_top_level_editable(tmp_path: Path, libdir_test: Path) -> None:
    (tmp_path / "fake_editable.pth").write_text(str(libdir_test))
    (meta_path := (tmp_path / "fake_editable-0.1.dist-info")).mkdir()
    (meta_path / "RECORD").write_text(f"fake_editable.pth,,\n{meta_path}/RECORD,,")

    assert set(_top_level_editable(PathDistribution(meta_path))) == {
        "basic",
        "dep",
        "mis_match",
        "namespace.package",
    }
