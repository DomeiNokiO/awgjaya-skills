# Web Injection — Tambalan per Kelas

Aturan inti: **data tak-tepercaya tak boleh menjadi kode/struktur.** Pisahkan data dari perintah di setiap sink.

## SQL Injection (sqli)
**Akar:** input user disatukan (string-concat) ke query SQL.
**Tambal:** parameterized query / prepared statement / ORM binding. JANGAN sanitasi manual/escape sendiri.
```python
# SALAH
cur.execute(f"SELECT * FROM users WHERE name='{name}'")
# BENAR
cur.execute("SELECT * FROM users WHERE name=%s", (name,))
```
```js
// BENAR (node-postgres)
db.query('SELECT * FROM users WHERE id=$1', [id]);
// ORM (Prisma/Sequelize) otomatis parameterized
```
- Identifier dinamis (nama kolom/tabel) TAK bisa diparameter → allow-list nilai yang diizinkan, jangan interpolasi mentah.
- Lapis kedua: DB user least-privilege (bukan `root`/`sa`), matikan `stacked queries` bila bisa.
**Grep sink:** `execute(f"`, `query('...' +`, `.raw(`, string concat dekat `SELECT|INSERT|UPDATE|DELETE`.
**Verifikasi:** payload `' OR '1'='1` dan `'; DROP--` tak lagi berpengaruh; nilai diperlakukan literal.

## NoSQL Injection
**Akar:** objek/operator user (`$gt`, `$where`) masuk query MongoDB.
**Tambal:** paksa tipe (cast ke string), tolak key berawalan `$`, pakai skema validasi (Joi/Zod). Jangan `find(req.body)` mentah.
```js
if (typeof req.body.user !== 'string') return res.sendStatus(400);
db.users.findOne({ user: req.body.user });
```

## Command Injection (cmdi)
**Akar:** input masuk ke shell (`system`, `exec`, backticks).
**Tambal:** JANGAN panggil shell. Pakai API arg-array tanpa shell.
```js
// SALAH
exec(`convert ${file} out.png`)
// BENAR
execFile('convert', [file, 'out.png'])   // tanpa shell, arg terpisah
```
```python
subprocess.run(['convert', file, 'out.png'])  # BUKAN shell=True
```
- Bila shell wajib: allow-list nilai; jangan andalkan escaping.
**Grep:** `shell=True`, `os.system`, `exec(`, `child_process.exec(`, backticks.

## SSTI (Server-Side Template Injection)
**Akar:** input user dirender sebagai template.
**Tambal:** jangan pernah `render_template_string(user_input)`. Pakai template statis + data sebagai variabel. Untuk template user, pakai engine logic-less/sandbox (Mustache, atau Jinja `SandboxedEnvironment`).
```python
# SALAH: render(f"Hello {name}")  BENAR: render_template('hi.html', name=name)
```

## XXE (XML External Entity) & XSLT
**Akar:** parser XML memproses DTD/external entity.
**Tambal:** nonaktifkan DTD & external entity di parser.
```python
from lxml import etree
p = etree.XMLParser(resolve_entities=False, no_network=True, dtd_validation=False)
```
```java
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setExpandEntityReferences(false);
```
- XSLT: matikan `document()`/extension function, jalankan di processor tanpa akses I/O.
- Berlaku juga untuk SVG/OOXML/SOAP yang di-parse.

## XSS (Cross-Site Scripting) & Dangling Markup
**Akar:** data tak-tepercaya masuk HTML tanpa encoding kontekstual.
**Tambal:**
- Default `textContent`/binding framework (React/Vue auto-escape), BUKAN `innerHTML`.
- Bila HTML wajib: sanitasi dengan DOMPurify (allow-list tag/atribut).
- Encoding sesuai konteks: HTML body, atribut, URL, JS, CSS berbeda aturan.
- Lapis kedua: `Content-Security-Policy` ketat (`script-src 'self'`, no `unsafe-inline`), `HttpOnly` cookie (curi sesi via XSS gagal), `X-Content-Type-Options: nosniff`.
```js
el.textContent = userName;                  // aman
el.innerHTML = DOMPurify.sanitize(userHtml); // bila HTML perlu
```
**Grep:** `innerHTML`, `outerHTML`, `document.write`, `dangerouslySetInnerHTML`, `v-html`, template `|safe`/`{{{ }}}`.

## CRLF / Header Injection
**Akar:** input masuk header/response tanpa strip `\r\n`.
**Tambal:** tolak/strip CR-LF dari nilai yang masuk header (redirect Location, Set-Cookie, log). Pakai API framework yang meng-encode header, jangan rakit string header sendiri.

## LDAP / lainnya
**Akar:** input ke filter LDAP.
**Tambal:** escape via API resmi (mis. `javax.naming` escaping) atau bind parameter; allow-list karakter.

## Pola verifikasi umum injeksi
1. Ulang payload PoC → diperlakukan sebagai data literal, bukan tereksekusi.
2. Grep seluruh repo untuk sink sejenis → semua ikut ditambal.
3. Tambah test: kirim payload klasik, assert response aman & tak ada efek samping.
