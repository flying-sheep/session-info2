"""Run tests in subprocesses."""


from collections.abc import AsyncGenerator
from importlib.metadata import version
from typing import Any

import pytest
from jupyter_client.asynchronous.client import AsyncKernelClient
from jupyter_client.manager import AsyncKernelManager


@pytest.fixture()
async def kernel_client() -> AsyncGenerator[AsyncKernelClient, None]:
    kernel_manager = AsyncKernelManager(kernel_name="python3")
    await kernel_manager.start_kernel()
    kernel_client = kernel_manager.client()
    yield kernel_client
    await kernel_manager.shutdown_kernel()


async def execute(kc: AsyncKernelClient, code: str) -> list[dict[str, str]]:
    await kc.wait_for_ready()
    msgs: list[dict[str, Any]] = []
    reply = await kc.execute_interactive(
        code,
        allow_stdin=False,
        output_hook=msgs.append,
        timeout=5.0,
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
            id="pytest",
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
    assert mimebundle == expected
