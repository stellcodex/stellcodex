import os
import json
import uuid
import redis
import chromadb
from datetime import datetime
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
STREAM_KEY = "stell:events:stream"
CHROMA_PATH = "/root/workspace/AI/vector_store"
TRUTH_PATH = "/root/workspace/_truth"
KNOWLEDGE_PATH = "/root/workspace/_knowledge"

# ─── EVENT SPINE ─────────────────────────────────────────────────────────────
def emit_event(etype, payload):
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "stellcodex.ai.indexer",
            "type": etype,
            "payload": payload,
            "correlation_id": str(uuid.uuid4())
        }
        r.xadd(STREAM_KEY, {"payload": json.dumps(event)})
        print(f"AI_EVENT | {etype} emitted.")
    except Exception as e:
        print(f"AI_EVENT_ERROR | {e}")

# ─── INDEXER ENGINE ───────────────────────────────────────────────────────────
def index_system_knowledge():
    """Tüm SSOT ve Bilgi belgelerini ChromaDB'ye indeksler."""
    print("AI | İndeksleme süreci başladı...")
    
    # ChromaDB client (Persistent)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name="stellcodex_knowledge")
    
    indexed_files = []
    
    # İndekslenecek dizinler
    target_paths = [Path(TRUTH_PATH), Path(KNOWLEDGE_PATH)]
    
    for base_path in target_paths:
        if not base_path.exists(): continue
        
        for md_file in base_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                # Basit bir chunking (parçalara bölme) simülasyonu
                # Daha büyük belgeler için chunker kullanılabilir
                collection.add(
                    documents=[content],
                    metadatas=[{"source": str(md_file), "name": md_file.name}],
                    ids=[str(uuid.uuid4())]
                )
                indexed_files.append(str(md_file))
                print(f"AI | Indexed: {md_file.name}")
            except Exception as e:
                print(f"AI_INDEX_ERROR | {md_file.name}: {e}")
    
    # Başarı eventi
    emit_event("ai.memory.synced", {
        "indexed_count": len(indexed_files),
        "files": [os.path.basename(f) for f in indexed_files],
        "chroma_path": CHROMA_PATH,
        "timestamp": datetime.now().isoformat()
    })
    
    print(f"AI | İndeksleme tamamlandı. Toplam {len(indexed_files)} dosya.")

if __name__ == "__main__":
    index_system_knowledge()
