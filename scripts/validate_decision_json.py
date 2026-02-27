#!/usr/bin/env python3
import json, sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

def main():
    if len(sys.argv) != 3:
        print("Usage: validate_decision_json.py <schema.json> <payload.json>", file=sys.stderr)
        sys.exit(2)

    schema_path = Path(sys.argv[1])
    payload_path = Path(sys.argv[2])

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    jsonschema.validate(instance=payload, schema=schema)
    print("PASS: decision_json schema valid")

if __name__ == "__main__":
    main()
