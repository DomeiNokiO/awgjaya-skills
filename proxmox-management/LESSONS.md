# Pelajaran Skill — Membangun Proxmox Dashboard

Rangkuman pelajaran teknis yang terkumpul selama membangun dashboard Proxmox realtime
(Node.js + Express + ws; vanilla JS + Tailwind + noVNC + xterm.js). Semua sudah masuk ke
`SKILL.md` sebagai aturan operasional; berkas ini menyajikannya sebagai ringkasan cepat yang
bisa dipakai ulang lintas proyek Proxmox lain.

Untuk log issue lengkap dengan gejala + solusi bertahap, lihat repo dashboard:
`docs/ISSUES-AND-SOLUTIONS.md`.

---

## Integrasi API Proxmox

1. **`fetch()` Node mengabaikan `https.Agent`** → self-signed gagal `fetch failed`
   (`DEPTH_ZERO_SELF_SIGNED_CERT`) walau `curl -k` sukses. Pakai `https.request` (zero-dep)
   atau `undici` dispatcher. `PVE_VERIFY_SSL=false` hanya efektif bila klien HTTP menerapkannya.
2. **Semua aksi mutasi balik UPID, bukan hasil.** WAJIB poll task sampai `exitstatus=OK` —
   jangan anggap sukses tanpa poll (gagal senyap).
3. **Create guest butuh `SDN.Use`** (PVE 8/9 cek zona SDN bridge), terpisah dari `VM.Allocate`.
   Terminal Node butuh `Sys.Console`. Token `--privsep 1` butuh ACL ke token, bukan cuma user.
4. **CPU `/cluster/resources` sudah pecahan 0–1 rata-rata semua core.** Cukup `cpu*100`;
   jangan kali ulang `maxcpu` atau ×100 dua kali.

## Menjalankan perintah DI DALAM CT tanpa akses host

5. **Dashboard tak punya shell host & Proxmox tak punya REST `pct exec`.** Untuk otomasi
   in-guest, buka **WS termproxy sendiri** dari backend:
   `POST /nodes/{n}/lxc/{vmid}/termproxy` → konek `vncwebsocket` dengan header token +
   `https.Agent`. Protokol: `user:ticket\n` → `1:cols:rows:` (WAJIB spawn PTY) →
   `0:len:payload`, akhiri `echo __MARKER__` untuk deteksi selesai.
6. **JANGAN simpan SSH root host di app** untuk `pct exec` — host = mahkota, app jebol = semua
   guest jebol. Jalur termproxy pakai token & privilege yang sama: nol kredensial baru.
7. **Buka SSH LXC: tulis drop-in `/etc/ssh/sshd_config.d/00-dashboard.conf`, bukan `sed`.**
   `sed` hanya mengganti baris yang ADA; template LXC sering tak punya baris
   `PasswordAuthentication` → sed diam → login ditolak (gejala: Termius menawarkan `password`
   tapi `Authentication failed`). Verifikasi nilai EFEKTIF dengan `sshd -T | grep -iE ...`.
   Password root harus benar-benar ter-set (template sering kunci root `!` di shadow →
   `passwd root`).

## Console / Terminal frontend

8. **CT pakai xterm.js + termproxy, bukan noVNC** (noVNC berat, teks tak bisa di-copy). VM
   tetap noVNC.
9. **noVNC import**: bundle ESM `@novnc/novnc@1.5.0/lib/rfb.js/+esm` (path `core/...` → 404),
   ambil `{ default: RFB }`.
10. **tmux** untuk persist: jangan kirim `cmd` termproxy (whitelist), ketik
    `tmux attach || tmux new` dari klien. Hanya untuk CT, bukan node host (`tmux && !isNode`).
11. **Auto-reconnect** console saat HP lock/background: tiket baru tiap konek, reconnect pada
    `disconnect`/`visibilitychange`, pagari reconnect-loop `if (r !== rfb) return`.
12. **Copy/paste HTTP**: `navigator.clipboard` diblokir non-secure → fallback textarea
    `execCommand` → overlay/prompt. Keyboard mobile: `<input>` opacity:0 DI DALAM viewport.

## Login & keamanan

13. **`DASHBOARD_PASSWORD` (plaintext) vs `DASHBOARD_PASSWORD_HASH` (scrypt siap-pakai).**
    Salah taruh hash di slot plaintext = server hash ulang = tak pernah cocok. Edit `.env`
    butuh restart.
14. **Jangan suruh user tempel hash** — smart-quote/terpotong. CLI interaktif `set-password`
    menulis `.env` sendiri. Verifikasi via `curl` login (200/401).
15. **Escape SEMUA data Proxmox** (nama VM/snapshot/volid) sebelum `innerHTML` — stored XSS.
    CSP + security headers sebagai lapis kedua. Token dibanding `timingSafeEqual`.
16. **Jangan percaya `X-Forwarded-For`** tanpa `TRUST_PROXY=true` (default false). Rate-limit
    juga di change-password, bukan cuma login. `Secure` cookie hanya di HTTPS.

## Installer / deploy (curl | bash)

17. **Prompt interaktif baca `/dev/tty`, bukan stdin** (stdin = skrip saat `bash <(curl ...)`).
18. **Guard `cp` sumber==tujuan** (`-ef` inode) + `cp -rT` idempotent; `set -Eeuo pipefail` +
    trap `$LINENO`/`$BASH_COMMAND`.
19. **update.sh jaga kepemilikan**: `safe.directory` + `git pull` sebagai owner + `chown` +
    `npm ci` hanya bila lockfile berubah.
20. **`export LC_ALL=C.UTF-8`** di awal (image CT minimal tak punya en_US.UTF-8).

## Performa

21. **Poll on-demand** (idle = 0 request), guard anti-overlap, skip node offline, interval
    >= 5 dtk, grafik pakai RRD (`rrddata` bawa cpu/mem/net/disk sekaligus). Footprint
    ± 50–70 MB, muat di LXC 1 vCPU/512 MB.

## UI

22. **Cache-bust `?v=N`** tiap rilis (HP cache agresif). Header mobile → dropdown `#menuDrop`.
    Ganti tema = remap CSS via `data-theme`, JANGAN ganti class di JS (zero-regresi). Tema
    "cerah" = remap netral `slate`, kecualikan `bg-black`/`text-white`. Aksi destruktif WAJIB
    `confirm()` per-aksi.
