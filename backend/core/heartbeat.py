from __future__ import annotations

import asyncio
import os
from typing import Optional

import httpx


async def heartbeat_loop(stop_event: asyncio.Event) -> None:
    interval = int(os.getenv("GEOSCOPE_HEARTBEAT_SECONDS", "300"))
    url = os.getenv("GEOSCOPE_HEALTHCHECK_URL", "http://127.0.0.1:8000/api/health")

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        while not stop_event.is_set():
            try:
                await client.get(url)
                print("[heartbeat] ok")
            except Exception as e:
                print(f"[heartbeat] failed: {e}")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass


def start_heartbeat() -> tuple[asyncio.Event, "asyncio.Task[None]"]:
    stop_event = asyncio.Event()
    task = asyncio.create_task(heartbeat_loop(stop_event))
    return stop_event, task

