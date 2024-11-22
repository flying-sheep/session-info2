# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os
import platform
import shutil
from multiprocessing import cpu_count
from pathlib import WindowsPath
from subprocess import CalledProcessError, run


def cpu_info() -> str:
    """Get CPU info."""
    proc = platform.processor() or None
    return f"{cpu_count()} logical CPU cores{f', {proc}' if proc else ''}"


def gpu_info() -> tuple[str, ...]:
    """Get GPU info."""
    nvidia_smi: str | WindowsPath
    if platform.system() == "Windows":
        # If the platform is Windows and nvidia-smi
        # could not be found from the environment path,
        # try to find it from system drive with default installation path
        nvidia_smi = shutil.which("nvidia-smi") or (
            WindowsPath(os.environ["SYSTEMDRIVE"])
            / r"\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
        )
    else:
        nvidia_smi = "nvidia-smi"

    # Get ID, processing and memory utilization for all GPUs
    try:
        p = run(
            [
                nvidia_smi,
                "--query-gpu=index,name,driver_version,memory.total",
                "--format=csv,noheader",
            ],
            capture_output=True,
            encoding="UTF-8",
            check=True,
        )
    except (CalledProcessError, FileNotFoundError):
        return ("No GPU found",)

    device_infos = (line.split(", ") for line in p.stdout.splitlines())
    return tuple(
        f"ID: {id_}, {name}, Driver: {driver}, Memory: {memory}"
        for id_, name, driver, memory in device_infos
    )
