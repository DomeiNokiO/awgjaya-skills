# Web Access & Auth — Tambalan per Kelas

Aturan inti: **otorisasi diputuskan di server, tiap request, deny-by-default.** Jangan percaya apa pun dari klien.

## IDOR / BOLA (Broken Object Level Authorization)
**Akar:** endpoint memakai ID dari request tanpa cek apakah user berhak atas objek itu.
**Tambal:** cek kepemilikan/izin objek di server sebelum aksi.
```js
const doc = await Doc.findById(req.params.id);
if (!doc || doc.ownerId !== req.user.id) return res.sendStatus(404); // 404, bukan 403 (jangan bocorkan eksistensi)
```
- Scope query ke user: `find({ _id:id, ownerId:req.user.id })`.
- Jangan pakai ID tebakan (sequential) sebagai satu-satunya kontrol → pakai UUID + tetap cek authz.
- Berlaku untuk SEMUA endpoint objek (GET/PUT/DELETE/list), bukan cuma yang dilaporkan.

## Authentication Bypass / 401-403 Bypass
**Akar:** authz diterapkan tak konsisten (mis. hanya di UI, atau bisa dilewati via method/path/header trick).
**Tambal:**
- Enforce authz di lapisan server (middleware) untuk semua route sensitif; deny-by-default (whitelist route publik, sisanya wajib auth).
- Normalisasi path sebelum cek (hindari `/admin/..;/`, trailing slash, case, URL-encoding bypass).
- Jangan andalkan header `X-Original-URL`/`X-Rewrite-URL`/`X-Forwarded-For` untuk keputusan akses.
- Verifikasi role di server tiap aksi, bukan dari klaim klien/hidden field.

## Path Traversal / LFI
**Akar:** input membentuk path file tanpa dibatasi.
**Tambal:** canonicalize lalu pastikan tetap di dalam base dir + allow-list nama.
```js
const base = '/srv/files';
const p = path.resolve(base, req.params.name);
if (!p.startsWith(base + path.sep)) return res.sendStatus(400);
```
```python
full = os.path.realpath(os.path.join(BASE, name))
if not full.startswith(BASE + os.sep): abort(400)
```
- Simpan file user di luar webroot; layani via handler yang cek izin, bukan path langsung.

## File Upload Tak Aman
**Akar:** file user diterima/dieksekusi tanpa validasi.
**Tambal:** allow-list ekstensi + MIME + magic-byte; nama acak (jangan pakai nama user); simpan di luar webroot / storage non-exec; batasi ukuran; `Content-Type` + `Content-Disposition: attachment` saat serve; matikan eksekusi di direktori upload (nginx `location` no PHP/CGI).
- Gambar: re-encode via library (buang payload polyglot).

## SSRF (Server-Side Request Forgery)
**Akar:** server fetch URL dari input tanpa batas.
**Tambal:**
- Allow-list host/domain tujuan; tolak selain itu.
- Resolve DNS lalu blok IP privat/loopback/link-local/metadata (`169.254.169.254`, `127.0.0.0/8`, `10/8`, `192.168/16`, `172.16/12`, `::1`, `fc00::/7`).
- Larang/kontrol redirect (redirect bisa lompat ke internal). Batasi skema ke `https`.
- Cek ulang IP SETELAH resolusi (cegah DNS rebinding — resolve sekali, konek ke IP itu).
- Cloud: pakai IMDSv2 / matikan metadata endpoint dari workload.

## CSRF
**Akar:** state-changing request tak butuh bukti niat user.
**Tambal:** token anti-CSRF (double-submit / synchronizer) untuk form; cookie `SameSite=Lax/Strict`; cek `Origin`/`Referer` untuk endpoint sensitif. API token-based (Authorization header, bukan cookie) umumnya imun.

## Open Redirect
**Akar:** parameter redirect dipakai mentah.
**Tambal:** allow-list tujuan relatif/host dikenal; tolak URL absolut ke host luar; jangan `Location: <input>`.

## CORS Misconfiguration
**Akar:** `Access-Control-Allow-Origin` reflektif + `Allow-Credentials: true`.
**Tambal:** allow-list origin eksplisit (jangan `*` dengan credentials, jangan reflect Origin tanpa cek). Batasi method/header.

## Clickjacking
**Tambal:** `Content-Security-Policy: frame-ancestors 'none'` (atau daftar izin) + `X-Frame-Options: DENY`.

## Session & Cookie
**Tambal:** cookie `HttpOnly; Secure; SameSite`; ID sesi acak kuat; regenerasi ID saat login (cegah fixation); expiry + idle timeout; invalidasi server-side saat logout. Rate-limit login.

## JWT / OAuth / OIDC / SAML
**JWT:** verifikasi signature; **pin algoritma** (tolak `alg:none`, tolak switch RS256→HS256); cek `exp`/`nbf`/`aud`/`iss`; jangan taruh data sensitif di payload; rotasi kunci. Jangan percaya klaim tanpa verifikasi.
**OAuth/OIDC:** validasi `redirect_uri` allow-list eksak; pakai `state` (anti-CSRF) + PKCE; verifikasi `iss`/`aud` id_token; jangan terima token dari sumber tak tepercaya.
**SAML:** verifikasi signature pada assertion (bukan hanya response); tolak comment-injection/XSW; pin issuer & audience; cek `NotOnOrAfter`.

## Rate Limiting / Brute Force
**Tambal:** rate-limit per-IP DAN per-akun di SEMUA endpoint verifikasi kredensial (login, reset, change-password, OTP). Lockout/backoff. Jangan percaya `X-Forwarded-For` kecuali di belakang proxy tepercaya (gate `TRUST_PROXY`).

## Verifikasi umum access/auth
1. Ulang PoC (akses objek orang lain / lewati auth) → sekarang 401/403/404.
2. Uji sebagai user A ambil resource user B → ditolak.
3. Test: request tanpa/dengan token salah → ditolak; dengan token benar tapi objek bukan miliknya → ditolak.
