from __future__ import annotations

import json

from cloudevents.http import CloudEvent, to_structured


def main() -> int:
    attributes = {
        "type": "stellcodex.ai.smoke",
        "source": "urn:stellcodex:ai:test",
    }
    data = {"status": "ok", "module": "event_smoke"}
    event = CloudEvent(attributes, data)
    headers, body = to_structured(event)
    payload = {
        "content_type": headers.get("content-type"),
        "body_preview": body.decode("utf-8"),
    }
    assert payload["content_type"] == "application/cloudevents+json"
    assert '"status": "ok"' in payload["body_preview"]
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
