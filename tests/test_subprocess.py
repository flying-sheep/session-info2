"""Run tests in subprocesses."""


from collections.abc import AsyncGenerator
from importlib.metadata import version
from typing import Any

import pytest
from jupyter_client.asynchronous.client import AsyncKernelClient
from jupyter_client.manager import start_new_async_kernel

from session_info2 import MIME_WIDGET


@pytest.fixture()
async def kernel_client() -> AsyncGenerator[AsyncKernelClient, None]:
    km, kc = await start_new_async_kernel(kernel_name="python3")
    yield kc
    kc.stop_channels()
    await km.shutdown_kernel()


async def execute(kc: AsyncKernelClient, code: str) -> list[dict[str, str]]:
    await kc.wait_for_ready()
    msgs: list[dict[str, Any]] = []
    reply = await kc.execute_interactive(
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
        pytest.param("", {"text/plain": ""}, id="empty"),
        pytest.param(
            "import pytest",
            {"text/plain": f"pytest\t{version('pytest')}"},
            id="package",
        ),
        pytest.param(
            "from jupyter_client import find_connection_file",
            {"text/plain": f"jupyter_client\t{version('jupyter-client')}"},
            id="function",
        ),
        pytest.param(
            "from jupyter_client.client import KernelClient",
            {"text/plain": f"jupyter_client\t{version('jupyter-client')}"},
            id="class",
        ),
    ],
)
async def test_run(
    kernel_client: AsyncKernelClient,
    code: str,
    expected: dict[str, str],
) -> None:
    await execute(kernel_client, code)
    [mimebundle] = await execute(kernel_client, RUN)
    assert mimebundle.keys() == {
        "text/plain",
        "text/markdown",
        "text/html",
        MIME_WIDGET,
    }
    assert mimebundle["text/plain"] == expected["text/plain"]
