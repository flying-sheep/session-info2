"""Run tests with artificial data."""
from __future__ import annotations

import re
from importlib.metadata import version
from typing import Any

import pytest
import testing.common.database as db
from jupyter_client.manager import KernelManager, run_kernel

from session_info2 import SessionInfo, _repr


@pytest.mark.parametrize(
    ("pkg2dists", "user_globals", "expected"),
    [
        pytest.param({}, {}, "", id="empty"),
        pytest.param(
            dict(pytest=["pytest"]),
            [pytest],
            f"pytest\t{version('pytest')}",
            id="package",
        ),
        pytest.param(
            dict(jupyter_client=["jupyter_client"]),
            [run_kernel],
            f"jupyter_client\t{version('jupyter-client')}",
            id="function",
        ),
        pytest.param(
            dict(jupyter_client=["jupyter_client"]),
            [KernelManager],
            f"jupyter_client\t{version('jupyter-client')}",
            id="class",
        ),
        pytest.param(
            {"testing.common.database": ["testing.common.database"]},
            [db],
            f"testing.common.database\t{version('testing.common.database')}",
            id="namespace_package",
        ),
    ],
)
def test_repr(
    pkg2dists: dict[str, list[str]],
    user_globals: list[Any],
    expected: str,
) -> None:
    si = SessionInfo(pkg2dists, {str(i): g for i, g in enumerate(user_globals)})
    r = repr(si)
    pkgs, info = r.split("\n----\t----\n") if "----" in r else ("", r)
    assert pkgs == expected
    assert re.fullmatch(
        "Python\t[^\n]+\nOS\t[^\n]+\nCPU\t[^\n]+\nUpdated\t[^\n]+", info, re.M
    )


@pytest.mark.parametrize(
    ("pkg2dists", "user_globals", "expected"),
    [
        pytest.param({}, {}, [], id="empty"),
        pytest.param(
            dict(pytest=["pytest"]),
            [pytest],
            [f"| pytest  | {version('pytest'):<7} |"],
            id="package",
        ),
        pytest.param(
            dict(jupyter_client=["jupyter_client"]),
            [run_kernel],
            [f"| jupyter_client | {version('jupyter-client'):<7} |"],
            id="function",
        ),
        # no need to test class again
    ],
)
def test_markdown(
    pkg2dists: dict[str, list[str]],
    user_globals: list[Any],
    expected: list[str],
) -> None:
    si = SessionInfo(pkg2dists, {str(i): g for i, g in enumerate(user_globals)})
    parts = _repr.repr_markdown(si).split("\n\n")
    if len(parts) > 1:
        pkg_str, info_str = parts

        pkg_header, pkg_sep, *pkg_rows = pkg_str.splitlines()
        if pkg2dists:
            [[pkg_name]] = pkg2dists.values()
            pkg_extra = len(pkg_name) - len("Package")
        else:
            pkg_extra = 0
        assert pkg_header == f"| Package{' ' * pkg_extra} | Version |"
        assert pkg_sep == f"| -------{'-' * pkg_extra} | ------- |"
        assert pkg_rows == expected
    else:
        [info_str] = parts

    info_header, info_sep, *info_rows = info_str.splitlines()
    info_extra = max(len(r.split("|")[2].strip()) for r in info_rows) - len("Info")
    assert info_header == f"| Component | Info{' ' * info_extra} |"
    assert info_sep == f"| --------- | ----{'-' * info_extra} |"
    # info_rows content is already tested for plain text, no need to test it again
