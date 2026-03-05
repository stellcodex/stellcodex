#!/usr/bin/env python3
import os
import signal
import sys
import time
import traceback
from typing import Any, List

import requests

STOP_REQUESTED = False


def _handle_signal(signum: int, _frame: Any) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True
    print(f"Received signal {signum}; stopping worker loop...")


def redis_command(base_url: str, token: str, command: List[str]) -> Any:
    endpoint = base_url.rstrip("/") + "/"
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {token}"},
        json=command,
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and "error" in payload:
        raise RuntimeError(f"Upstash error: {payload['error']}")
    if isinstance(payload, dict):
        return payload.get("result")
    return payload


def main() -> int:
    queue_key = os.getenv("STELLCODEX_QUEUE_KEY", "stellcodex:queue")
    print(f"STELLCODEX worker starting. queue_key={queue_key}")

    required = ["UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("Missing required environment variables: " + ", ".join(missing))
        return 2

    redis_url = os.environ["UPSTASH_REDIS_REST_URL"]
    redis_token = os.environ["UPSTASH_REDIS_REST_TOKEN"]
    poll_sleep_seconds = float(os.getenv("STELLCODEX_POLL_SLEEP_SECONDS", "2"))
    error_backoff_seconds = float(os.getenv("STELLCODEX_ERROR_BACKOFF_SECONDS", "5"))

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    print("Worker loop started.")
    idle_counter = 0

    while not STOP_REQUESTED:
        try:
            item = redis_command(redis_url, redis_token, ["LPOP", queue_key])
            if item is None:
                idle_counter += 1
                if idle_counter == 1 or idle_counter % 30 == 0:
                    print(f"No item in queue '{queue_key}' (idle poll #{idle_counter}).")
                time.sleep(poll_sleep_seconds)
                continue

            idle_counter = 0
            print(f"Dequeued message from '{queue_key}': {str(item)[:200]}")
            # Placeholder for message processing logic.
        except Exception as exc:
            print(f"Worker error: {exc}")
            traceback.print_exc()
            time.sleep(error_backoff_seconds)

    print("Worker stopped cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
