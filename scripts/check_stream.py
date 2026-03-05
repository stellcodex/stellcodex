#!/root/workspace/AI/.venv/bin/python3
import redis
import json

r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
messages = r.xread({'stell:events:stream': '0'}, count=100)

if not messages:
    print("No messages.")
else:
    for stream, msgs in messages:
        for mid, data in msgs:
            print(f"ID: {mid}")
            payload = data.get('payload')
            if payload:
                try:
                    p = json.loads(payload)
                    print(f"  Type: {p.get('type')}")
                    if p.get('type') == 'whatsapp.message.received':
                        print(f"  Text: {p['payload']['text']}")
                except:
                    print(f"  Raw: {payload[:50]}...")
