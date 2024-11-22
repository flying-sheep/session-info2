# SPDX-License-Identifier: MPL-2.0
"""Test helper utils."""

from __future__ import annotations

import pytest

from session_info2 import _mods


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
