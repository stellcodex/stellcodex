#!/root/workspace/AI/.venv/bin/python3
import json
import uuid
import sys
import argparse
from datetime import datetime, timezone
import redis

REDIS_URL = "redis://127.0.0.1:6379/0"
STREAM_KEY = "stell:events:stream"

def send_whatsapp(text, sender="+905000000000"):
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    
    event = {
        "event_id": f"wa-{uuid.uuid4()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "whatsapp.gateway",
        "type": "whatsapp.message.received",
        "payload": {
            "sender": sender,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    r.xadd(STREAM_KEY, {"payload": json.dumps(event, ensure_ascii=True)})
    print(f"WhatsApp message sent to stream: '{text}' from {sender}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate WhatsApp message.")
    parser.add_argument("text", help="Message text")
    parser.add_argument("--sender", default="+905000000000", help="Sender phone number")
    args = parser.parse_args()
    
    send_whatsapp(args.text, args.sender)
