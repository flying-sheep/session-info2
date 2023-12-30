"""Run tests with artificial data."""

from importlib.metadata import version
from typing import Any

import pytest
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
    ],
)
def test_repr(
    pkg2dists: dict[str, list[str]],
    user_globals: list[Any],
    expected: str,
) -> None:
    si = SessionInfo(pkg2dists, {str(i): g for i, g in enumerate(user_globals)})
    assert repr(si) == expected
