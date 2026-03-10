/**
 * Stell — Cloudflare Workers Webhook
 * Sunucudan BAĞIMSIZ çalışır. Sunucu çökse de Stell aktif.
 *
 * Secrets (Cloudflare Dashboard → Settings → Variables):
 *   WHATSAPP_TOKEN       - Meta WhatsApp Cloud API token
 *   WEBHOOK_VERIFY_TOKEN - Meta webhook doğrulama tokeni
 *   STELL_OWNER_PHONE    - Yetkili telefon numarası (90XXXXXXXXXX)
 *   GITHUB_TOKEN         - GitHub PAT (repo okuma/yazma)
 *   GITHUB_REPO          - örn: "kullaniciadi/stell-assistant"
 *   BACKEND_URL          - örn: "https://stellcodex.com/api/v1"
 *   BACKEND_ADMIN_TOKEN  - Stellcodex admin JWT (opsiyonel, sunucu komutları için)
 */

const GRAPH_API = "https://graph.facebook.com/v19.0";
const GITHUB_RAW = "https://raw.githubusercontent.com";
const GITHUB_API = "https://api.github.com";

// ── Komut bilgi haritası ───────────────────────────────────────────────────
const KNOWLEDGE_MAP = {
  platform:  "knowledge/operations/stellcodex-platform.md",
  urun:      "knowledge/products/stellcodex-overview.md",
  "ürün":    "knowledge/products/stellcodex-overview.md",
  faq:       "knowledge/faq/genel-sss.md",
  sss:       "knowledge/faq/genel-sss.md",
  ai:        "knowledge/automation/ai-models.md",
  modeller:  "knowledge/automation/ai-models.md",
  komutlar:  "playbooks/whatsapp/komutlar.md",
  admin:     "playbooks/admin/platform-ops.md",
  guvenlik:  "policies/security/access.md",
  "güvenlik":"policies/security/access.md",
  onay:      "policies/approval/required-approvals.md",
  whatsapp:  "policies/channels/whatsapp.md",
};

// ── Webhook entry point ────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname !== "/stell/webhook") {
      return new Response("Not Found", { status: 404 });
    }

    if (request.method === "GET") {
      return handleVerification(request, env);
    }
    if (request.method === "POST") {
      return handleMessage(request, env);
    }
    return new Response("Method Not Allowed", { status: 405 });
  },
};

// ── Meta webhook doğrulama ─────────────────────────────────────────────────
function handleVerification(request, env) {
  const url = new URL(request.url);
  const mode      = url.searchParams.get("hub.mode");
  const token     = url.searchParams.get("hub.verify_token");
  const challenge = url.searchParams.get("hub.challenge");

  if (mode === "subscribe" && token === env.WEBHOOK_VERIFY_TOKEN) {
    return new Response(challenge, { status: 200 });
  }
  return new Response("Forbidden", { status: 403 });
}

// ── Gelen mesaj işleme ─────────────────────────────────────────────────────
async function handleMessage(request, env) {
  const body = await request.json().catch(() => null);
  if (!body) return new Response("OK");

  try {
    const change  = body.entry?.[0]?.changes?.[0]?.value;
    if (!change || change.statuses) return new Response("OK");

    const message = change.messages?.[0];
    if (!message) return new Response("OK");

    const sender = message.from;
    const mtype  = message.type;

    // Sadece yetkili numara
    if (sender !== env.STELL_OWNER_PHONE) return new Response("OK");

    if (mtype === "text") {
      const text  = message.text.body.trim();
      const reply = await processCommand(text, env);
      await sendWhatsApp(sender, reply, env);
    } else if (mtype === "document") {
      const fname = message.document?.filename || "belge";
      await appendToGitHub("genois/inbox/questions.md",
        `\n- [${now()}] 📎 Belge alındı: ${fname}`, env);
      await sendWhatsApp(sender, `📎 Belge alındı: *${fname}*\nDrive'a kaydedildi.`, env);
    }
  } catch (e) {
    console.error("Hata:", e);
  }

  return new Response("OK");
}

// ── Komut yönlendirme ──────────────────────────────────────────────────────
async function processCommand(text, env) {
  const t  = text.trim();
  const tl = t.toLowerCase();

  // Selamlama
  if (["merhaba", "selam", "hi", "hello", "hey"].includes(tl)) {
    return "👋 Merhaba! Ben Stell.\nKomutlar için `yardım` yaz.";
  }

  // Yardım
  if (["yardım", "yardim", "?", "help"].includes(tl)) {
    const topics = Object.keys(KNOWLEDGE_MAP).join(", ");
    return (
      "📋 *Stell Komutları*\n\n" +
      "• `durum` — Platform durumu\n" +
      "• `not: <metin>` — Not kaydet\n" +
      "• `notlar` — Son notlar\n" +
      "• `bilgi: <konu>` — Bilgi göster\n" +
      `  Konular: ${topics}\n\n` +
      "• `log: backend|worker|redis` — Sunucu logu\n\n" +
      "Bilinmeyen sorular inbox'a kaydedilir."
    );
  }

  // Platform durumu → sunucu API'sine sor
  if (tl === "durum") {
    return await callBackend("/admin/health", env);
  }

  // Not kaydet → GitHub'a yaz
  if (tl.startsWith("not:")) {
    const note = t.slice(4).trim();
    if (!note) return "Not metni boş. Örnek: `not: Müşteri ile Salı 14:00 görüşme`";
    await appendToGitHub("genois/inbox/notes.md",
      `\n- [${now()}] ${note}`, env);
    return `✅ Not kaydedildi:\n_${note}_`;
  }

  // Notları listele → GitHub'dan oku
  if (["notlar", "notlarım"].includes(tl)) {
    const content = await readFromGitHub("genois/inbox/notes.md", env);
    const lines   = content.split("\n").filter(l => l.startsWith("- [")).slice(-5);
    return lines.length
      ? "📝 *Son Notlar:*\n\n" + lines.join("\n")
      : "Henüz not yok.";
  }

  // Bilgi sorgula → GitHub raw okuma
  if (tl.startsWith("bilgi:")) {
    const konu = t.slice(6).trim().toLowerCase();
    const path = KNOWLEDGE_MAP[konu];
    if (!path) {
      return `Bilinmeyen konu. Geçerliler: ${Object.keys(KNOWLEDGE_MAP).join(", ")}`;
    }
    const content = await readFromGitHub(path, env);
    return content.length > 3800 ? content.slice(0, 3800) + "\n...(kısaltıldı)" : content;
  }

  // Log sorgula → sunucu API
  if (tl.startsWith("log:")) {
    const svc = t.slice(4).trim().toLowerCase();
    const allowed = ["backend", "worker", "redis", "postgres"];
    if (!allowed.includes(svc)) {
      return `Geçerli servisler: ${allowed.join(", ")}`;
    }
    return await callBackend(`/admin/logs/${svc}`, env);
  }

  // AI delegasyon prefix → inbox'a kaydet
  for (const prefix of ["claude:", "gemini:", "codex:", "abacus:"]) {
    if (tl.startsWith(prefix)) {
      const model = prefix.replace(":", "");
      const task  = t.slice(prefix.length).trim();
      await appendToGitHub("genois/inbox/questions.md",
        `\n- [${now()}] [${model.toUpperCase()} görevi] ${task}`, env);
      return (
        `📥 _${model}_ görevi inbox'a kaydedildi.\n` +
        `Görev: _${task.slice(0, 200)}_`
      );
    }
  }

  // Bilinmeyen → inbox
  await appendToGitHub("genois/inbox/questions.md",
    `\n- [${now()}] ❓ ${t}`, env);
  return `❓ Anlamadım, inbox'a kaydettim.\nYardım için \`yardım\` yaz.`;
}

// ── Sunucu API çağrısı (sunucu yoksa graceful hata) ───────────────────────
async function callBackend(path, env) {
  if (!env.BACKEND_URL) return "⚠️ Backend URL ayarlanmamış.";
  try {
    const headers = {};
    if (env.BACKEND_ADMIN_TOKEN) {
      headers["Authorization"] = `Bearer ${env.BACKEND_ADMIN_TOKEN}`;
    }
    const res = await fetch(`${env.BACKEND_URL}${path}`, {
      headers,
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) {
      if (res.status === 503 || res.status === 502) {
        return "⚠️ Sunucu şu an erişilemiyor. Diğer komutlar çalışmaya devam ediyor.";
      }
      const err = await res.json().catch(() => ({}));
      return `❌ Hata (${res.status}): ${err.detail || res.statusText}`;
    }
    const data = await res.json();
    // Health endpoint formatı
    if (data.api || data.db) {
      const lines = Object.entries(data).map(([k, v]) => {
        const icon = v === "ok" ? "✅" : "❌";
        return `${icon} ${k}: ${v}`;
      });
      return "📊 *Sunucu Durumu:*\n" + lines.join("\n");
    }
    return JSON.stringify(data, null, 2).slice(0, 2000);
  } catch (e) {
    if (e.name === "TimeoutError") {
      return "⚠️ Sunucu yanıt vermedi (zaman aşımı). Stell Edge'de çalışmaya devam ediyor.";
    }
    return `⚠️ Sunucu bağlantı hatası: ${e.message}`;
  }
}

// ── GitHub raw dosya okuma ─────────────────────────────────────────────────
async function readFromGitHub(path, env) {
  if (!env.GITHUB_REPO) return "GitHub repo ayarlanmamış.";
  try {
    const url = `${GITHUB_RAW}/${env.GITHUB_REPO}/master/${path}`;
    const headers = env.GITHUB_TOKEN
      ? { Authorization: `token ${env.GITHUB_TOKEN}` }
      : {};
    const res = await fetch(url, { headers });
    if (!res.ok) return `Dosya bulunamadı: ${path}`;
    return await res.text();
  } catch (e) {
    return `GitHub okuma hatası: ${e.message}`;
  }
}

// ── GitHub'a dosya ekleme (append) ────────────────────────────────────────
async function appendToGitHub(path, content, env) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_REPO) return;
  const apiUrl = `${GITHUB_API}/repos/${env.GITHUB_REPO}/contents/${path}`;
  try {
    // Mevcut dosyayı al (sha için)
    const getRes = await fetch(apiUrl, {
      headers: {
        Authorization: `token ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github.v3+json",
      },
    });
    let existingContent = "";
    let sha = undefined;
    if (getRes.ok) {
      const data = await getRes.json();
      existingContent = atob(data.content.replace(/\n/g, ""));
      sha = data.sha;
    }
    // Yeni içerik
    const newContent = existingContent + content;
    const encoded    = btoa(unescape(encodeURIComponent(newContent)));
    // Commit
    await fetch(apiUrl, {
      method: "PUT",
      headers: {
        Authorization: `token ${env.GITHUB_TOKEN}`,
        "Content-Type": "application/json",
        Accept: "application/vnd.github.v3+json",
      },
      body: JSON.stringify({
        message: `stell: ${path.split("/").pop()} güncellendi [${now()}]`,
        content: encoded,
        ...(sha ? { sha } : {}),
      }),
    });
  } catch (e) {
    console.error("GitHub yazma hatası:", e);
  }
}

// ── WhatsApp mesaj gönder ──────────────────────────────────────────────────
async function sendWhatsApp(to, text, env) {
  const phoneId = env.PHONE_NUMBER_ID;
  if (!phoneId || !env.WHATSAPP_TOKEN) return;
  const body = {
    messaging_product: "whatsapp",
    to,
    type: "text",
    text: { body: text.length > 4000 ? text.slice(0, 4000) + "\n...(kısaltıldı)" : text },
  };
  await fetch(`${GRAPH_API}/${phoneId}/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.WHATSAPP_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  }).catch(e => console.error("WhatsApp gönderim hatası:", e));
}

// ── Yardımcı ──────────────────────────────────────────────────────────────
function now() {
  return new Date().toISOString().slice(0, 16).replace("T", " ");
}
