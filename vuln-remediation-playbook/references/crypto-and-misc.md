# Kripto & Lain-lain — Tambalan per Kelas

Aturan inti: **pakai primitif/pustaka teruji dengan mode aman; jangan bikin sendiri.**

## Password Storage
**Akar:** password di-hash lemah (MD5/SHA1/SHA256 telanjang) atau plaintext.
**Tambal:** hash lambat + salt: **argon2id** (utama), atau bcrypt/scrypt. Per-user salt acak (built-in). Jangan pepper di kode. Verifikasi timing-safe.
```python
from argon2 import PasswordHasher
ph = PasswordHasher(); h = ph.hash(pw); ph.verify(h, pw)
```
- Migrasi: re-hash saat login berikutnya.

## RSA Misuse
**Tambal:** kunci >= 2048-bit (idealnya 3072+); padding **OAEP** untuk enkripsi, **PSS** untuk signature (bukan PKCS#1 v1.5 / textbook RSA); jangan reuse modulus; jangan e kecil tanpa padding; pakai library (cryptography/OpenSSL), bukan implementasi sendiri. Verifikasi signature dengan benar (cek nilai balik, bukan hanya "tidak error").

## Hash Attacks (length extension, weak)
**Tambal:** untuk MAC pakai **HMAC** (bukan `hash(secret||msg)` — rentan length-extension) atau SHA-3/BLAKE2. Bandingkan digest timing-safe. Jangan pakai MD5/SHA1 untuk keamanan.

## Symmetric Cipher Misuse
**Tambal:** AEAD (**AES-GCM** atau **ChaCha20-Poly1305**) — memberi kerahasiaan + integritas. JANGAN ECB (bocor pola); jangan CBC tanpa MAC (padding oracle); **nonce/IV unik per pesan** (jangan reuse, khususnya GCM); kunci dari KDF/CSPRNG, bukan konstanta. Enkripsi lalu autentikasi (atau pakai AEAD yang sudah menggabungkan).

## Insecure Deserialization
**Akar:** deserialisasi data tak-tepercaya (pickle/Java serial/PHP unserialize/YAML unsafe) → RCE.
**Tambal:** JANGAN deserialisasi data dari user dengan format yang bisa meng-instantiate objek arbitrer. Pakai format data murni (JSON) + skema validasi. Bila wajib: allow-list kelas (RestrictedUnpickler / `ObjectInputFilter` Java / `yaml.safe_load`), tanda-tangani payload (HMAC) sebelum percaya.
```python
import yaml; yaml.safe_load(data)   # BUKAN yaml.load
# pickle: hindari untuk input eksternal, titik.
```

## Prototype Pollution (JS)
**Akar:** merge/set path rekursif dari input user mengubah `Object.prototype`.
**Tambal:** tolak key `__proto__`/`constructor`/`prototype` saat merge; pakai `Map` untuk data key-value dinamis; `Object.create(null)` untuk dict; `Object.freeze(Object.prototype)` sebagai lapis; pakai lib merge aman (lodash ter-patch) & skema validasi (Zod/Ajv `additionalProperties:false`).

## Race Condition / TOCTOU
**Akar:** cek-lalu-pakai tanpa atomisitas (mis. cek saldo lalu potong, dua request paralel).
**Tambal:** transaksi DB + row lock (`SELECT ... FOR UPDATE`) atau operasi atomik (`UPDATE ... WHERE balance>=x`); unique constraint; idempotency key untuk request sekali-jalan; hindari window cek→aksi. Untuk file: buka dengan flag atomik (`O_CREAT|O_EXCL`).

## HTTP Request Smuggling
**Akar:** front-end & back-end beda tafsir `Content-Length` vs `Transfer-Encoding`.
**Tambal:** pakai server/proxy yang menolak pesan ambigu (CL+TE bersamaan); normalisasi/rewrite di edge; HTTP/2 end-to-end bila bisa; jangan reuse koneksi downstream secara berbahaya. Update proxy/web server ke versi ber-patch.

## HTTP Host Header Attacks
**Tambal:** jangan pakai `Host` untuk membangun URL absolut (reset link, dsb); allow-list host yang valid; set canonical host di config; validasi `Host`/`X-Forwarded-Host`.

## HTTP Parameter Pollution
**Tambal:** tentukan perilaku parameter duplikat secara eksplisit; framework konsisten first/last; validasi tipe & jumlah; jangan gabung mentah ke query downstream.

## Subdomain Takeover
**Tambal:** hapus DNS record dangling (CNAME ke layanan yang sudah tak di-claim); audit rutin; claim/hapus resource sebelum lepas DNS.

## Business Logic
**Akar:** alur bisa dilewati/diurutkan ulang (skip pembayaran, kupon negatif, kuantitas negatif).
**Tambal:** validasi invariant di server (harga, kuantitas>0, status transisi sah); jangan percaya harga/total dari klien — hitung ulang server-side; enforce urutan state machine; batasi/kuota; audit trail.

## Verifikasi umum
1. Ulang PoC (padding oracle, pollution, race, logic bypass) → gagal.
2. Uji nilai batas (negatif, nol, duplikat, paralel) → ditolak/aman.
3. Test regresi meng-encode PoC ditambahkan.
