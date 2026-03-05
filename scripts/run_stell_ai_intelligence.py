#!/root/workspace/AI/.venv/bin/python3
import os
import sys

# Add AI/ directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "AI"))

from stell_ai.daemon import run_forever

if __name__ == "__main__":
    print("STELL AI - STARTING INTELLIGENCE AND LEARNING DAEMON...")
    print("Mode: Proactive Apprentice | Memory: Hybrid RAG | Interface: Event Spine")
    try:
        run_forever()
    except KeyboardInterrupt:
        print("\nDaemon stopped by user.")
    except Exception as e:
        print(f"\nDaemon failed: {e}")
        sys.exit(1)
