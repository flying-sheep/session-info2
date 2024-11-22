# SPDX-License-Identifier: MPL-2.0
"""Run tests in subprocesses."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import pytest
from jupyter_client.manager import start_new_async_kernel

from session_info2._repr import MIME_WIDGET

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable
    from pathlib import Path

    from jupyter_client.asynchronous.client import AsyncKernelClient

    Execute = Callable[[str], Awaitable[list[dict[str, str]]]]


@pytest.fixture(scope="session")
async def kernel_client() -> AsyncGenerator[AsyncKernelClient, None]:
    km, kc = await start_new_async_kernel(kernel_name="python3")
    yield kc
    kc.stop_channels()
    await km.shutdown_kernel()  # pyright: ignore[reportUnknownMemberType]


@pytest.fixture
async def execute(
    kernel_client: AsyncKernelClient, libdir_test: Path
) -> AsyncGenerator[Execute, None]:
    async def execute(code: str) -> list[dict[str, str]]:
        await kernel_client.wait_for_ready()
        msgs: list[dict[str, Any]] = []
        reply = await kernel_client.execute_interactive(  # pyright: ignore[reportUnknownMemberType]
            code,
            allow_stdin=False,
            output_hook=msgs.append,
            # If it hangs, enable this: timeout=5.0,
        )
        if reply["content"]["status"] == "error":
            content = reply["content"]
            content["traceback"] = "\n".join(content["traceback"])
            pytest.fail("{ename}: {evalue}\n{traceback}".format_map(content))
        elif reply["content"]["status"] != "ok":
            pytest.fail(f"Unexpected reply status: {reply['content']['status']}")
        return [
            msg["content"]["data"]
            for msg in msgs
            if msg["header"]["msg_type"] == "execute_result"
        ]

    await execute(
        f"""
        #from pyinstrument import Profiler as _Profiler
        #_profiler = _Profiler()
        #_profiler.start()
        import sys
        sys.path.insert(0, {json.dumps(str(libdir_test))})
        del sys
        """
    )
    yield execute
    await execute(
        """
        #_profiler.stop()
        #_profiler.open_in_browser()
        import site
        from importlib import reload
        reload(site)
        %reset
        """
    )


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
async def test_run(execute: Execute, code: str, expected: str) -> None:
    await execute(code)
    [mimebundle] = await execute(RUN)
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
    assert re.fullmatch(
        "Python\t[^\n]+\nOS\t[^\n]+\nUpdated\t[^\n]+", info, re.MULTILINE
    )
