#!/root/workspace/AI/.venv/bin/python3
import os
import sys
import json
from datetime import datetime, timezone

# Add AI/ directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "AI"))

from stell_ai.listener import EventListener
from stell_ai.planner import Planner
from stell_ai.executor import Executor

def debug_one():
    print("DEBUG: Initializing components...")
    listener = EventListener()
    planner = Planner()
    executor = Executor()
    
    print(f"DEBUG: Group={listener.group}, Consumer={listener.consumer}, Stream={listener.stream_key}")
    
    # Try to recreate group from 0 to capture previous messages
    try:
        listener.redis.xgroup_create(listener.stream_key, listener.group, id="0", mkstream=True)
        print("DEBUG: Group recreated from 0.")
    except Exception:
        pass

    print("DEBUG: Polling for messages (5s timeout)...")
    messages = listener.poll(block_ms=5000)
    
    if not messages:
        print("DEBUG: No messages found.")
        return

    for message_id, fields in messages:
        print(f"DEBUG: Processing message {message_id}...")
        actions = planner.plan(fields)
        print(f"DEBUG: Planned actions: {actions}")
        
        # Check if it's a WhatsApp message manually
        payload = fields.get("payload", "{}")
        try:
            envelope = json.loads(payload)
            if envelope.get("type") == "whatsapp.message.received":
                print("DEBUG: Detected WhatsApp message.")
                text = envelope["payload"]["text"]
                print(f"DEBUG: Message text: {text}")
                
                # Execute context sync
                executor.execute({
                    "action": "sync_context",
                    "payload": {"key": "debug_wa", "value": text}
                })
                print("DEBUG: Context synced.")
                
                # Execute query
                print("DEBUG: Querying memory...")
                res = executor.execute({
                    "action": "query_memory",
                    "payload": {"query": text, "top_k": 1}
                })
                print(f"DEBUG: Search result found: {len(res.get('results', []))} items.")
                if res.get('results'):
                    print(f"DEBUG: Top result: {res['results'][0]['title']}")
                
                # Execute follow-up
                print("DEBUG: Generating follow-up question...")
                q = executor.execute({
                    "action": "generate_learning_question",
                    "payload": {"target": text[:15]}
                })
                print(f"DEBUG: Generated question: {q.get('question')}")
        except Exception as e:
            print(f"DEBUG: Error in manual parse: {e}")

        for action in actions:
            print(f"DEBUG: Executing planned action {action['action']}...")
            result = executor.execute(action)
            print(f"DEBUG: Result: {result}")
            
        listener.ack(message_id)
        print(f"DEBUG: Message {message_id} ACKed.")

if __name__ == "__main__":
    debug_one()
