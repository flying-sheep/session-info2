"""Run tests with artificial data."""
from __future__ import annotations

from importlib.metadata import version
from typing import Any

import pytest
import testing.common.database as db
from jupyter_client.manager import KernelManager, run_kernel

from session_info2 import SessionInfo


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
    assert repr(si) == expected


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
    header, sep, *rows = si._repr_markdown_().splitlines()  # noqa: SLF001
    if pkg2dists:
        [[pkg_name]] = pkg2dists.values()
        extra = len(pkg_name) - 7
    else:
        extra = 0
    assert header == f"| Package{' ' * extra} | Version |"
    assert sep == f"| -------{'-' * extra} | ------- |"
    assert rows == expected
