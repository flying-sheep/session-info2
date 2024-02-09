"""Run tests in subprocesses."""
from __future__ import annotations

import re
from importlib.metadata import version
from typing import TYPE_CHECKING, Any

import pytest
from jupyter_client.manager import start_new_async_kernel

from session_info2._repr import MIME_WIDGET

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from jupyter_client.asynchronous.client import AsyncKernelClient


@pytest.fixture()
async def kernel_client() -> AsyncGenerator[AsyncKernelClient, None]:
    km, kc = await start_new_async_kernel(kernel_name="python3")
    yield kc
    kc.stop_channels()
    await km.shutdown_kernel()  # pyright: ignore[reportUnknownMemberType]


async def execute(kc: AsyncKernelClient, code: str) -> list[dict[str, str]]:
    await kc.wait_for_ready()
    msgs: list[dict[str, Any]] = []
    reply = await kc.execute_interactive(  # pyright: ignore[reportUnknownMemberType]
        code,
        allow_stdin=False,
        output_hook=msgs.append,
        # If it hangs, enable this: timeout=5.0,
    )
    assert reply["content"]["status"] == "ok"
    return [
        msg["content"]["data"]
        for msg in msgs
        if msg["header"]["msg_type"] == "execute_result"
    ]


RUN = """\
from session_info2 import session_info

session_info()
"""


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        pytest.param("", "", id="empty"),
        pytest.param(
            "import pytest",
            f"pytest\t{version('pytest')}",
            id="package",
        ),
        pytest.param(
            "from jupyter_client import find_connection_file",
            f"jupyter_client\t{version('jupyter-client')}",
            id="function",
        ),
        pytest.param(
            "from jupyter_client.client import KernelClient",
            f"jupyter_client\t{version('jupyter-client')}",
            id="class",
        ),
        pytest.param(
            "import testing.common.database as db",
            f"testing.common.database\t{version('testing.common.database')}",
            id="namespace_package",
        ),
    ],
)
async def test_run(
    kernel_client: AsyncKernelClient,
    code: str,
    expected: str,
) -> None:
    await execute(kernel_client, code)
    [mimebundle] = await execute(kernel_client, RUN)
    assert mimebundle.keys() == {
        "text/plain",
        "text/markdown",
        "text/html",
        "application/json",
        MIME_WIDGET,
    }
    r = mimebundle["text/plain"]
    pkgs, info = r.split("\n----\t----\n") if "----" in r else ("", r)
    assert pkgs == expected
    # No CPU info by default
    assert re.fullmatch("Python\t[^\n]+\nOS\t[^\n]+\nUpdated\t[^\n]+", info, re.M)
