#!/usr/bin/env python3
import os
import sys

import requests  # noqa: F401
import redis  # noqa: F401


def main() -> int:
    queue_key = os.getenv("STELLCODEX_QUEUE_KEY", "stellcodex:queue")
    print(f"STELLCODEX worker starting. queue_key={queue_key}")

    required = ["UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("Missing required environment variables: " + ", ".join(missing))
        return 1

    print("Environment looks good; worker bootstrap completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
