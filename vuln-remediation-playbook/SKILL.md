---
name: vuln-remediation-playbook
description: "Use when patching a vuln. Root cause, fix, verify."
version: 1.0.0
author: Wahyu, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Security, Remediation, Patching, Hardening, AppSec, DefensiveSecurity]
    related_skills: [pentest-playbook, requesting-code-review, proxmox-management]
---

# Vulnerability Remediation Playbook

Pasangan **defensif** dari playbook serang (pentest-playbook + hack-skills). Playbook serang menemukan lubang; skill ini **menambalnya dengan benar**: dari akar masalah, bukan tambal gejala. Untuk tiap temuan → akar penyebab → tambalan konkret (dengan contoh kode) → verifikasi bahwa lubang benar-benar tertutup dan tak ada regresi.

## When to Use

- Ada laporan pentest/scan/CVE dan kamu harus **memperbaikinya**, bukan mengeksploitasi.
- Code review menemukan pola berbahaya (mis. query string-concat, `innerHTML` data user).
- Hardening proaktif sebuah service sebelum rilis.
- Menutup temuan dari `pentest-playbook` (fase Report → fase Fix).

Don't use for: menyerang sistem, menulis exploit, atau bypass pertahanan (itu domain pentest-playbook, authorized-only).

## Prinsip Tambalan (jangan dilanggar)

1. **Tambal akar, bukan gejala.** Blokir satu payload = gejala. Ganti mekanisme rentan (mis. parameterisasi query) = akar. Blacklist payload hampir selalu bisa di-bypass; whitelist/desain aman tidak.
2. **Positive security model.** Allow-list (apa yang boleh) mengalahkan deny-list (apa yang dilarang). Validasi = bandingkan ke bentuk yang diharapkan, tolak selain itu.
3. **Defense in depth.** Satu tambalan bisa gagal; pasang lapis kedua (mis. parameterized query + least-privilege DB user + WAF). Tapi lapis luar TIDAK menggantikan perbaikan akar.
4. **Fail closed.** Saat ragu/error, tolak akses — jangan default-allow.
5. **Jangan roll-your-own crypto/auth/parser.** Pakai pustaka teruji (argon2/bcrypt, library JWT, parser XML aman). Kode buatan sendiri = sumber bug baru.
6. **Verifikasi menutup, cek tak ada regresi.** Ulangi PoC serang → harus gagal. Jalankan test suite → fungsi normal tetap jalan.
7. **Least privilege di mana-mana.** Token, DB user, service account, file permission: beri hak minimum. Membatasi blast-radius saat tambalan lain jebol.

## Alur Patch Universal (7 langkah)

1. **Reproduksi & pahami.** Konfirmasi PoC dari laporan. Tanpa reproduksi, kamu menebak. Catat request/input persis yang memicu.
2. **Cari akar penyebab, bukan titik gejala.** Telusuri data dari sumber (input user) ke sink (query/exec/HTML/file). Akar = tempat data tak-tepercaya menyentuh operasi sensitif tanpa perlindungan.
3. **Petakan semua sink sejenis.** Satu SQLi biasanya berarti ada 10 query lain berpola sama. Grep seluruh codebase untuk pola tersebut (lihat referensi per-kelas). Tambal SEMUA, bukan yang dilaporkan saja.
4. **Terapkan tambalan akar** (lihat referensi domain di bawah untuk pola per-kelas).
5. **Tambah lapis pertahanan** (security headers, least-privilege, rate-limit) sesuai konteks.
6. **Verifikasi:** (a) ulangi PoC → gagal; (b) test suite hijau; (c) grep pola lama → nol sisa; (d) tambah regression test yang meng-encode PoC agar tak kambuh.
7. **Dokumentasikan:** apa akarnya, kenapa tambalan ini benar, di mana saja diterapkan. Untuk laporan pentest, tautkan finding-ID → commit.

## Reference Files (buka saat menangani kelasnya)

- `references/web-injection.md` — SQLi, NoSQLi, command injection, SSTI, XXE, XSS, CRLF, XSLT, LDAP. (sink-based fixes)
- `references/web-access-auth.md` — IDOR/BOLA, auth bypass, path traversal/LFI, file upload, SSRF, CSRF, open redirect, CORS, clickjacking, session/cookie, JWT/OAuth/SAML, rate-limit.
- `references/infra-hardening.md` — privesc Linux/Windows, AD, container/K8s escape, lateral movement, exposed services, network/TLS, secrets management, dependency/supply-chain.
- `references/crypto-and-misc.md` — RSA/hash/symmetric misuse, password storage, deserialization, prototype pollution, race condition, request smuggling, business logic, host-header, HPP, subdomain takeover.

## Mapping serang -> tambal (indeks cepat)

| Kelas serang (hack-skills) | Akar tambalan | Referensi |
|---|---|---|
| sqli / nosql | Parameterized query / ORM binding | web-injection |
| xss / dangling-markup | Output encoding kontekstual + CSP | web-injection |
| cmdi / expression-language / jndi | Hindari shell; execFile arg-array; allow-list | web-injection |
| ssti | Sandbox / logic-less template; jangan render input | web-injection |
| xxe / xslt | Nonaktifkan DTD & external entity di parser | web-injection |
| idor / bola | Otorisasi per-objek server-side (bukan ID tebakan) | web-access-auth |
| path-traversal / lfi / upload | Canonicalize + allow-list path/type; simpan di luar webroot | web-access-auth |
| ssrf | Allow-list host + blok IP internal/metadata; no-redirect | web-access-auth |
| csrf | Token anti-CSRF + SameSite cookie | web-access-auth |
| authbypass / 401-403-bypass | Enforce authz di server tiap request; deny-by-default | web-access-auth |
| jwt / oauth / saml | Verifikasi signature+alg pin, aud/iss/exp, jangan trust client | web-access-auth |
| linux/windows privesc | Least-priv, patch, hapus SUID/misconfig, no creds di disk | infra-hardening |
| active-directory-* / ntlm-relay | Signing/EPA, tiering, ACL hardening, LAPS | infra-hardening |
| container/k8s escape | Non-root, drop caps, seccomp, no privileged, RBAC | infra-hardening |
| dependency-confusion | Pin registry+scope, lockfile, integrity hash | infra-hardening |
| deserialization | Jangan deser data tak-tepercaya; allow-list tipe | crypto-and-misc |
| prototype-pollution | Freeze proto, tolak __proto__, Map bukan objek | crypto-and-misc |
| race-condition | Lock/transaksi atomik, idempotency key | crypto-and-misc |
| rsa/hash/symmetric | Pustaka teruji, mode aman (AEAD), no ECB, kunci kuat | crypto-and-misc |
| password storage | argon2id/bcrypt + salt, jangan MD5/SHA1 telanjang | crypto-and-misc |
| request-smuggling / host-header | Normalisasi di proxy, tolak ambigu CL/TE | crypto-and-misc |

## Verification Checklist

- [ ] PoC asli diulang → sekarang GAGAL (bukti utama tambalan bekerja)
- [ ] Semua sink sejenis di codebase ikut ditambal (grep bersih), bukan hanya yang dilaporkan
- [ ] Tambalan menyerang akar (parameterisasi/allow-list/authz server-side), bukan blacklist payload
- [ ] Lapis kedua terpasang bila relevan (headers, least-priv, rate-limit)
- [ ] Regression test yang meng-encode PoC ditambahkan (cegah kambuh)
- [ ] Test suite fungsional hijau (tak ada regresi fitur)
- [ ] Fail-closed pada error/kondisi tak terduga
- [ ] Secret tak ter-commit; least-privilege diverifikasi
- [ ] Untuk laporan pentest: tiap finding-ID tertaut ke commit/PR tambalan
