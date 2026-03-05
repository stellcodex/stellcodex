#!/root/workspace/AI/.venv/bin/python3
import json
import uuid
import sys
import argparse
from datetime import datetime, timezone
import redis

REDIS_URL = "redis://127.0.0.1:6379/0"
STREAM_KEY = "stell:events:stream"

def main():
    parser = argparse.ArgumentParser(description="Teach STELL AI new knowledge.")
    parser.add_argument("--category", default="engineering", help="Category (engineering, manufacturing, etc.)")
    parser.add_argument("--title", required=True, help="Title of the knowledge")
    parser.add_argument("--content", required=True, help="Content to store")
    parser.add_argument("--tags", help="Comma separated tags")
    
    args = parser.parse_args()
    
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    
    event = {
        "event_id": f"learn-{uuid.uuid4()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "stell.cli.learn",
        "type": "ai.learning.ingest",
        "payload": {
            "category": args.category,
            "title": args.title,
            "content": args.content,
            "metadata": {
                "tags": args.tags.split(",") if args.tags else [],
                "author": "human-teacher"
            }
        }
    }
    
    r.xadd(STREAM_KEY, {"payload": json.dumps(event, ensure_ascii=True)})
    print(f"Knowledge ingestion event emitted for: {args.title} [{args.category}]")

if __name__ == "__main__":
    main()
