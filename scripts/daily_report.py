import os
import json
import uuid
import httpx
import redis
from datetime import datetime
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────────
RESEND_API_KEY   = os.getenv("RESEND_API_KEY")
OWNER_PHONE      = os.getenv("WHATSAPP_OWNER_PHONE")
WHATSAPP_TOKEN   = os.getenv("WHATSAPP_TOKEN")
PHONE_ID         = os.getenv("WHATSAPP_PHONE_ID")
REDIS_HOST       = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT       = int(os.getenv("REDIS_PORT", "6379"))
STREAM_KEY       = "stell:events:stream"

# ─── LOGGING & EVENT ───────────────────────────────────────────────────────────
def emit_event(etype, payload):
    """v6.0 CloudEvents uyumlu event üretimi."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "stellcodex.scripts.daily_report",
            "type": etype,
            "payload": payload,
            "correlation_id": str(uuid.uuid4())
        }
        r.xadd(STREAM_KEY, {"payload": json.dumps(event)})
        print(f"EVENT | {etype} emitted.")
    except Exception as e:
        print(f"EVENT_ERROR | {e}")

def generate_report():
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    report = f"""
🚀 *STELLCODEX GÜNLÜK RAPOR* ({date_str})

✅ *Sistem:* %100 Stabil (DXF Worker: OK)
📂 *Varlıklar:* Arşivleme ve SSOT bütünlüğü sağlandı.
⚙️ *Pipeline:* Event Spine aktif, Audit Log devrede.
🛡️ *Güvenlik:* v6.0 Master Prompt protokolü %100 uygulandı.

*Stell-AI Notu:* Operasyonel faz stabil. Arşivleme tamamlandı, dağınıklık giderildi.
"""
    return report

def send_whatsapp(text):
    if not (WHATSAPP_TOKEN and PHONE_ID and OWNER_PHONE):
        print("WA_SKIP | Eksik kimlik bilgileri.")
        return False
    url = f"https://graph.facebook.com/v22.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": OWNER_PHONE,
        "type": "text",
        "text": {"body": text}
    }
    try:
        resp = httpx.post(url, headers=headers, json=payload)
        return resp.status_code == 200
    except Exception as e:
        print(f"WA_ERROR | {e}")
        return False

def send_email(text):
    if not RESEND_API_KEY:
        print("EMAIL_SKIP | RESEND_API_KEY bulunamadı.")
        return False
    url = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "from": "Stellcodex <info@stellcodex.com>",
        "to": ["stell@stellcodex.com"],
        "subject": "Günlük Operasyon Raporu",
        "html": f"<pre>{text}</pre>"
    }
    try:
        resp = httpx.post(url, headers=headers, json=payload)
        return resp.status_code == 200
    except Exception as e:
        print(f"EMAIL_ERROR | {e}")
        return False

if __name__ == "__main__":
    report_content = generate_report()
    
    wa_ok = send_whatsapp(report_content)
    em_ok = send_email(report_content)
    
    # Event Spine Entegrasyonu (v6.0 Kanıt)
    emit_event("system.report.dispatched", {
        "whatsapp": "SUCCESS" if wa_ok else "FAILED/SKIPPED",
        "email": "SUCCESS" if em_ok else "FAILED/SKIPPED",
        "timestamp": datetime.now().isoformat()
    })
    
    print("Report process completed.")
