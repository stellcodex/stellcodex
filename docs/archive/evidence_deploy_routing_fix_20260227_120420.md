# Evidence: Deploy Routing Verification (No Change Needed)

- Timestamp: 2026-02-27 12:04:20 (+03:00 server local)
- Host: production
- Repo: /var/www/stellcodex
- Current commit: `e067252` (`Add redeploy trigger to README`)

## Conclusion

Routing is already correct and public traffic serves the same HTML as local Next.js runtime.
No NGINX or PM2 config change was required.

## Runtime verification

Command:

```bash
pm2 info stellcodex-next
```

Key output:

- status: `online`
- script args: `start -p 3010 -H 127.0.0.1`
- exec cwd: `/var/www/stellcodex/frontend`

Command:

```bash
ss -ltnp | egrep ':(80|443|3010|3000|3001)\\b'
```

Output (key lines):

- `0.0.0.0:80` -> `nginx`
- `0.0.0.0:443` -> `nginx`
- `127.0.0.1:3010` -> `next-server`

## NGINX routing verification

Command:

```bash
grep -R --line-number "proxy_pass" /etc/nginx/sites-enabled /etc/nginx/nginx.conf 2>/dev/null
```

Output:

```text
/etc/nginx/sites-enabled/stellcodex:39:    proxy_pass http://127.0.0.1:8000;
/etc/nginx/sites-enabled/stellcodex:54:    proxy_pass http://127.0.0.1:9000/;
/etc/nginx/sites-enabled/stellcodex:68:    proxy_pass http://127.0.0.1:9000;
/etc/nginx/sites-enabled/stellcodex:81:    proxy_pass http://127.0.0.1:8000/health;
/etc/nginx/sites-enabled/stellcodex:113:proxy_pass http://127.0.0.1:3010;
/etc/nginx/sites-enabled/stellcodex-api:21:    proxy_pass http://127.0.0.1:8000;
```

Command:

```bash
sed -n '1,220p' /etc/nginx/sites-enabled/stellcodex
```

Verified in active `location /` block:

- `proxy_pass http://127.0.0.1:3010;`
- `proxy_set_header Upgrade $http_upgrade;`
- `proxy_set_header Connection $connection_upgrade;`

## Local vs public content verification

Commands:

```bash
curl -sS -I http://127.0.0.1:3010
curl -sS -I https://stellcodex.com
curl -sS http://127.0.0.1:3010 | sha256sum
curl -sS https://stellcodex.com | sha256sum
```

Header excerpts (local):

```text
HTTP/1.1 200 OK
x-nextjs-cache: HIT
x-powered-by: Next.js
cache-control: s-maxage=31536000
etag: "1639efxtonx7lv"
```

Header excerpts (public):

```text
HTTP/2 200
server: cloudflare
x-nextjs-cache: HIT
x-powered-by: Next.js
cf-cache-status: DYNAMIC
```

SHA256 comparison:

- Local (`127.0.0.1:3010`): `78366846114a4f340fceb22560c88bcf264228b5b37353545395dee4cc430f86`
- Public (`https://stellcodex.com`): `78366846114a4f340fceb22560c88bcf264228b5b37353545395dee4cc430f86`

Result: exact match.

## Root cause assessment

At verification time, there is no routing mismatch. Public and local responses are identical.
If old UI was seen previously, the likely transient cause was client/browser cache or stale edge observation before latest checks.
