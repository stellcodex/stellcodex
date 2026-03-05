#!/usr/bin/env python3
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import sys

# Add AI/ directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "AI"))

from stell_ai.config import (
    KNOWLEDGE_BASE_DIR, 
    SOLVED_CASES_DIR, 
    DATASETS_DIR, 
    INGEST_REPORT_PATH
)

def get_report():
    print("="*60)
    print("STELL AI - INTELLIGENCE AND LEARNING REPORT")
    print("="*60)
    print(f"Report Date: {datetime.now(timezone.utc).isoformat()}")
    
    # 1. RAG Ingestion Status
    if INGEST_REPORT_PATH.exists():
        with INGEST_REPORT_PATH.open("r") as f:
            report = json.loads(f.read())
            print("\nRAG Memory Status:")
            print(f" - Last Rebuild: {report.get('timestamp')}")
            print(f" - Indexed Chunks: {report.get('indexed_chunks')}")
            print(f" - Indexed Sources: {report.get('indexed_sources')}")
            by_type = report.get("by_doc_type", {})
            for k, v in by_type.items():
                print(f"   * {k}: {v}")
    
    # 2. Knowledge Base
    print("\nKnowledge Base (Structured):")
    if KNOWLEDGE_BASE_DIR.exists():
        for cat in sorted(KNOWLEDGE_BASE_DIR.iterdir()):
            if cat.is_dir():
                files = list(cat.glob("*.md"))
                print(f" - {cat.name}: {len(files)} docs")
            
    # 3. Solved Cases (Learning Loop)
    solved = list(SOLVED_CASES_DIR.glob("*.md"))
    print("\nLearning Loop (Solved Cases):")
    print(f" - Total Solved Cases: {len(solved)}")
    
    # 4. Dataset Generation
    datasets = list(DATASETS_DIR.glob("*.jsonl"))
    print("\nTraining Datasets Generated:")
    print(f" - Total Datasets: {len(datasets)}")
    for ds in datasets:
        size = ds.stat().st_size / 1024
        print(f"   * {ds.name} ({size:.2f} KB)")
        
    print("\n" + "="*60)

if __name__ == "__main__":
    get_report()
