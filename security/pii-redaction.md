# PII Redaction Kurallari (Audit Log)

Amac: audit_log.payload_redacted alanina PII, token veya secret dusmesini kesin olarak engellemek.

## Mutlak Yasak Alanlar (tam sil)
Asagidaki anahtarlar payload icinde gorunurse tamamen kaldirilir:
- password, pass, pwd
- access_token, refresh_token, id_token, jwt, bearer
- api_key, secret, client_secret, private_key
- authorization header
- session cookie / set-cookie
- raw file content / base64 blobs

## Maskeleme (kismi)
- Email: a***@domain.com formatinda maskele
- IP: /24 veya /64 truncation ya da hash
- Telefon: son 2-4 hane gorunur
- User-Agent: gerekiyorsa hash

## Hashleme (geri donussuz izleme)
Su alanlar plaintext yerine SHA-256 (saltli) hash ile saklanir:
- share token / public link token (mutlaka)
- device identifiers (varsa)

## Allow-list Yaklasimi
payload_redacted icine yalnizca su tip alanlar yazilabilir:
- target_type, target_id
- action params (ornegin expiry_days)
- state transitions (from -> to)
- counts (affected_items)
- policy flag name + value
- correlation ids (request_id, trace_id)

## Zorunlu Kurallar
- Audit insert oncesi tek bir redaction katmani kullanilir.
- Audit loga dogrudan raw payload insert edilmez.
- logs.export_full gibi aksiyonlar sadece Owner + approval ile calisir.
