"""Secure shell command helpers."""
from __future__ import annotations

import asyncio
import shlex
import subprocess
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


class ShellCommandError(RuntimeError):
    def __init__(self, command: Sequence[str], returncode: int, stdout: str, stderr: str):
        super().__init__(
            f"Command failed with exit code {returncode}: {' '.join(map(shlex.quote, command))}"
        )
        self.command = list(command)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@dataclass(slots=True)
class CommandResult:
    command: Sequence[str]
    stdout: str
    stderr: str
    returncode: int

    def succeeded(self) -> bool:
        return self.returncode == 0


def _run_sync(
    command: Sequence[str],
    *,
    timeout: int | float = 60,
    env: Mapping[str, str] | None = None,
    check: bool = True,
) -> CommandResult:
    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=dict(env) if env else None,
        text=True,
    )
    result = CommandResult(
        command=command,
        stdout=process.stdout.strip(),
        stderr=process.stderr.strip(),
        returncode=process.returncode,
    )
    if check and process.returncode != 0:
        raise ShellCommandError(command, process.returncode, result.stdout, result.stderr)
    return result


async def run_cmd(
    command: Sequence[str] | str,
    *,
    timeout: int | float = 60,
    env: Mapping[str, str] | None = None,
    check: bool = True,
) -> CommandResult:
    if isinstance(command, str):
        args: Iterable[str] = shlex.split(command)
    else:
        args = command

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        lambda: _run_sync(tuple(args), timeout=timeout, env=env, check=check),
    )


__all__ = ["run_cmd", "ShellCommandError", "CommandResult"]
