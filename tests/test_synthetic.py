"""Run tests with artificial data."""

from importlib.metadata import version
from typing import Any

import pytest
from jupyter_client import find_connection_file
from session_info2 import SessionInfo


@pytest.mark.parametrize(
    ("pkg2dists", "user_globals", "expected"),
    [
        pytest.param({}, {}, "", id="empty"),
        pytest.param(
            dict(pytest=["pytest"]),
            dict(pytest=pytest),
            f"pytest\t{version('pytest')}",
            id="package",
        ),
        pytest.param(
            dict(jupyter_client=["jupyter_client"]),
            dict(find_connection_file=find_connection_file),
            f"jupyter_client\t{version('jupyter-client')}",
            id="function",
        ),
    ],
)
def test_repr(
    pkg2dists: dict[str, list[str]],
    user_globals: dict[str, Any],
    expected: dict[str, str],
) -> None:
    si = SessionInfo(pkg2dists, user_globals)
    assert repr(si) == expected
