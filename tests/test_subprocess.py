"""Run tests in subprocesses."""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import pytest
from jupyter_client.manager import start_new_async_kernel

from session_info2._repr import MIME_WIDGET

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from jupyter_client.asynchronous.client import AsyncKernelClient


@pytest.fixture()
async def kernel_client(test_libdir: Path) -> AsyncGenerator[AsyncKernelClient, None]:
    km, kc = await start_new_async_kernel(kernel_name="python3")
    await execute(
        kc,
        f"""
        import sys
        sys.path.insert(0, {json.dumps(str(test_libdir))})
        del sys
        """,
    )
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
    assert reply["content"]["status"] == "ok", reply["content"]["evalue"]
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
        pytest.param("import basic", "basic\t1.0", id="package"),
        pytest.param("from basic import fn", "basic\t1.0", id="function"),
        pytest.param("from basic import Cls", "basic\t1.0", id="class"),
        pytest.param(
            "import namespace.package as nsp",
            "namespace.package\t2.2.1",
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
