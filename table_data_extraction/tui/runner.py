from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from queue import Empty, Queue
import subprocess
import threading

from .models import CompletedCommand, StreamChunk, SubprocessCommand

OutputCallback = Callable[[StreamChunk], None]


def _read_stream(
    pipe,
    *,
    stream_name: str,
    queue: Queue[tuple[str, str] | None],
) -> None:
    try:
        for line in iter(pipe.readline, ""):
            queue.put((stream_name, line))
    finally:
        pipe.close()
        queue.put(None)


def run_subprocess_command(
    command: SubprocessCommand,
    *,
    on_output: OutputCallback | None = None,
    cancel_event: threading.Event | None = None,
    env: Mapping[str, str] | None = None,
) -> CompletedCommand:
    if not command.argv:
        raise ValueError("Command argv must not be empty.")

    process = subprocess.Popen(
        command.argv,
        cwd=Path(command.cwd),
        env=dict(env) if env is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None
    assert process.stderr is not None

    queue: Queue[tuple[str, str] | None] = Queue()
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    active_readers = 2
    cancelled = False

    stdout_reader = threading.Thread(
        target=_read_stream,
        kwargs={
            "pipe": process.stdout,
            "stream_name": "stdout",
            "queue": queue,
        },
        daemon=True,
    )
    stderr_reader = threading.Thread(
        target=_read_stream,
        kwargs={
            "pipe": process.stderr,
            "stream_name": "stderr",
            "queue": queue,
        },
        daemon=True,
    )
    stdout_reader.start()
    stderr_reader.start()

    while active_readers > 0:
        if cancel_event is not None and cancel_event.is_set() and not cancelled:
            cancelled = True
            process.terminate()

        try:
            item = queue.get(timeout=0.05)
        except Empty:
            if process.poll() is not None and not stdout_reader.is_alive() and not stderr_reader.is_alive():
                break
            continue

        if item is None:
            active_readers -= 1
            continue

        stream_name, text = item
        chunk = StreamChunk(stream=stream_name, text=text)
        if stream_name == "stdout":
            stdout_parts.append(text)
        else:
            stderr_parts.append(text)
        if on_output is not None:
            on_output(chunk)

    try:
        returncode = process.wait(timeout=1 if cancelled else None)
    except subprocess.TimeoutExpired:
        process.kill()
        returncode = process.wait()

    return CompletedCommand(
        command=command,
        returncode=returncode,
        stdout="".join(stdout_parts),
        stderr="".join(stderr_parts),
        was_cancelled=cancelled,
    )
