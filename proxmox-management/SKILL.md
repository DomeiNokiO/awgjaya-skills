---
name: proxmox-management
description: "Mengelola VM, container, dan integrasi API Proxmox VE."
version: 1.4.0
author: Wahyu, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Proxmox, Virtualization, API, DevOps, LXC, QEMU]
    related_skills: [secure-laravel-delivery]
---

# Proxmox Management Skill

Panduan lengkap untuk mengotomatisasi dan mengelola Proxmox VE (PVE) 7.x/8.x lewat API REST, CLI (`qm`/`pct`/`pvesh`/`pvesm`), dan integrasi aplikasi. Mencakup autentikasi, siklus hidup VM/CT, provisioning cloud-init, cloning/template, snapshot, backup/restore, storage, networking, firewall, HA/migrasi, dan monitoring.

## When to Use

- Membangun dashboard/script otomasi untuk mengontrol VM (QEMU) & container (LXC).
- Provisioning terprogram: clone template, inject cloud-init, resize disk, atur network.
- Backup/restore terjadwal (vzdump), snapshot sebelum deploy, rollback.
- Integrasi aplikasi (mis. Laravel/Node waralaba) dengan orkestrasi Proxmox.
- Migrasi VM antar node, konfigurasi HA, firewall, dan monitoring resource.
- Membangun dashboard realtime (WebSocket) untuk kontrol VM/CT, snapshot, backup, migrasi, grafik histori, multi-node, dan console VNC. Implementasi acuan: repo privat `DomeiNokiO/proxmox-dashboard` (Node.js+Express+ws, vanilla JS+Tailwind).

Don't use for:
- Instalasi/hardening hypervisor Proxmox itu sendiri (bare-metal setup).
- Cloud publik (AWS/GCP/Azure) atau hypervisor lain (VMware/Hyper-V).

## Prerequisites

- **Konektivitas API:** Port `8006` (web/API) terbuka. SSH `22` untuk operasi CLI langsung.
- **Kredensial (pilih salah satu):**
  - **API Token (DIREKOMENDASIKAN):** `USER@REALM!TOKENID=SECRET`. Tanpa CSRF, tanpa ticket, tidak kedaluwarsa. Buat via `pveum`.
  - **Ticket (password):** `root@pam` + password → dapat `PVEAuthCookie` + `CSRFPreventionToken` (berlaku ~2 jam).
- **SSL:** Default self-signed. Client harus bypass verifikasi (`verify=False` / `rejectUnauthorized:false`) ATAU pasang CA proper untuk produksi. **Peringatan:** `PVE_VERIFY_SSL` default `false` di `pve.py` berarti TANPA verifikasi cert — hanya untuk LAN tepercaya/testing. Di jaringan tak tepercaya set `PVE_VERIFY_SSL=true` + pasang CA (tanpa verifikasi = rentan MITM, token bisa dicuri).
- **Env vars** (lihat `.env` di reference): `PVE_HOST`, `PVE_NODE`, `PVE_TOKEN_ID`, `PVE_TOKEN_SECRET`.

### Membuat API Token + role minimal (di node Proxmox)

```bash
# terminal: buat user, role, token, dan assign privilege
pveum user add automation@pve
pveum role add Automational -privs "VM.Allocate VM.Config.Disk VM.Config.CPU VM.Config.Memory VM.Config.Network VM.Config.Options VM.Config.Cloudinit VM.PowerMgmt VM.Snapshot VM.Clone VM.Audit VM.Console Datastore.AllocateSpace Datastore.Audit Sys.Audit SDN.Use"
# SDN.Use WAJIB: PVE 8.x/9.x menolak create CT/VM tanpa ini dengan 403 (/sdn/zones/localnetwork/vmbrN, SDN.Use), meski VM.Allocate ada. Tambah ke role yang sudah ada: pveum role modify Automational -privs "...SDN.Use" (izin berlaku instan, tanpa restart).
pveum aclmod / -user automation@pve -role Automational
pveum user token add automation@pve automate --privsep 0
# Simpan value token yang ditampilkan SEKALI ini ke PVE_TOKEN_SECRET
```

## How to Run

Semua aksi terprogram jalankan lewat `terminal`:

```
terminal(command="python3 skills/devops/proxmox-management/scripts/pve.py <cmd> ...", timeout=120)
```

Helper `scripts/pve.py` (client Python berbasis token, lihat file) menyediakan subcommand: `nodes`, `list`, `status`, `config`, `start/stop/shutdown/reboot`, `clone`, `set-cloudinit`, `resize`, `snapshot`, `rollback`, `backup`, `delete`, `task-wait`. Semua argumen `vmid`/`snapshot`/`disk`/`node` divalidasi (regex) & tiap segmen path di-quote sebelum masuk API — cegah path/parameter injection. Untuk ad-hoc, gunakan `pvesh` di node via SSH.

## Quick Reference (CLI di node Proxmox)

```bash
# --- Inventaris ---
pvesh get /nodes                         # daftar node
qm list                                  # daftar VM di node ini
pct list                                 # daftar container
pvesh get /cluster/resources --type vm   # semua VM/CT cluster (JSON)

# --- Lifecycle VM (qm) / CT (pct) ---
qm start 100 ; qm shutdown 100 ; qm stop 100 ; qm reboot 100
pct start 200 ; pct shutdown 200 ; pct stop 200
qm status 100 ; pct status 200

# --- Clone dari template ---
qm clone 9000 150 --name web-01 --full --storage local-lvm

# --- Cloud-init (VM template ber-cloud-init) ---
qm set 150 --ciuser deploy --cipassword '***' --sshkeys ~/.ssh/id_ed25519.pub
qm set 150 --ipconfig0 ip=192.168.1.150/24,gw=192.168.1.1
qm set 150 --nameserver 1.1.1.1 --searchdomain lan
qm cloudinit update 150

# --- Disk & resource ---
qm resize 150 scsi0 +20G
qm set 150 --memory 4096 --cores 2
qm set 150 --net0 virtio,bridge=vmbr0,tag=10   # VLAN tag 10

# --- Snapshot ---
qm snapshot 150 pre-deploy --description "before app deploy"
qm rollback 150 pre-deploy
qm delsnapshot 150 pre-deploy

# --- Backup / restore (vzdump) ---
vzdump 150 --storage local --mode snapshot --compress zstd
qmrestore /var/lib/vz/dump/vzdump-qemu-150-*.vma.zst 151 --storage local-lvm
pct restore 251 /var/lib/vz/dump/vzdump-lxc-250-*.tar.zst --storage local-lvm

# --- Migrasi antar node ---
qm migrate 150 node2 --online --with-local-disks

# --- Storage & template ---
pvesm status                             # status storage
pveam update && pveam available          # daftar template LXC
pveam download local ubuntu-24.04-standard_24.04-2_amd64.tar.zst

# --- Firewall ---
pve-firewall status
qm set 150 --firewall 1
```

## Procedure

### 1. Autentikasi API
- **Token (pilihan utama):** kirim header `Authorization: PVEAPIToken=USER@REALM!TOKENID=SECRET` pada setiap request. Tidak butuh cookie/CSRF. Selesai bila `GET /version` balas 200.
- **Ticket:** `POST /api2/json/access/ticket` dengan `username`+`password` → simpan `ticket` sebagai cookie `PVEAuthCookie` dan `CSRFPreventionToken` sebagai header untuk semua POST/PUT/DELETE. Selesai bila ticket diterima.

### 2. Siklus hidup VM/CT
- Aksi via `POST /api2/json/nodes/{node}/{type}/{vmid}/status/{action}` (`type` = `qemu`|`lxc`).
- Setiap aksi mutasi mengembalikan **UPID** (task id). Poll `GET /nodes/{node}/tasks/{upid}/status` sampai `status=stopped`; cek `exitstatus=OK`. Selesai bila task OK.

### 3. Provisioning dari template + cloud-init
- Clone: `POST /nodes/{node}/qemu/{template}/clone` (`newid`, `name`, `full=1`).
- Set cloud-init: `PUT /nodes/{node}/qemu/{vmid}/config` dengan `ciuser`, `sshkeys` (URL-encoded), `ipconfig0`, `nameserver`.
- Resize: `PUT .../resize` (`disk=scsi0`, `size=+20G`). Start, lalu verifikasi SSH masuk. Selesai bila VM boot & reachable.

### 4. Snapshot sebelum perubahan berisiko
- `POST .../snapshot` sebelum deploy; `POST .../snapshot/{name}/rollback` untuk balik. Selalu snapshot sebelum operasi destruktif. Selesai bila snapshot muncul di `GET .../snapshot`.

### 5. Backup terjadwal & restore
- Backup: `POST /nodes/{node}/vzdump` (`vmid`, `storage`, `mode=snapshot`, `compress=zstd`). Untuk jadwal, buat entry di `Datacenter > Backup` atau via `POST /cluster/backup`.
- Restore: `qmrestore`/`pct restore` ke vmid baru untuk hindari menimpa. Selesai bila VM hasil restore start OK.

### 6. Hapus VM/CT (aman)
- Pastikan `status=stopped` dulu, baru `DELETE /nodes/{node}/{type}/{vmid}` (`purge=1` untuk hapus dari job backup/HA juga). Selesai bila vmid hilang dari `list`.

## Reference Files

- `references/api-endpoints.md` — peta endpoint API lengkap (nodes, qemu, lxc, storage, cluster, firewall, HA, tasks).
- `references/cli-cheatsheet.md` — `qm`/`pct`/`pvesh`/`pvesm`/`pveum`/`vzdump` per kategori.
- `references/cloud-init-networking.md` — template cloud-init, IP statis/DHCP, VLAN, dual-NIC, contoh Ubuntu.
- `references/nodejs-integration.md` — client Axios (token & ticket), pola async task-wait, `qs` payload.
- `references/lxc-installer.md` — pola installer LXC paste-ready (curl|bash), create-ct.sh, systemd unit, pitfall cp/locale/Node-detect.
- `scripts/pve.py` — CLI Python siap pakai (token auth, task polling, subcommand lengkap).

## Performa: bikin integrasi RINGAN di Proxmox

Proxmox mudah terbebani bila polling serampangan. Aturan wajib untuk dashboard/monitor:

- **Poll on-demand, bukan 24/7.** Jalankan loop status HANYA saat ada client (browser WS) terbuka; hentikan saat client terakhir tutup. Idle harus = 0 request ke Proxmox.
- **Guard anti-overlap.** Simpan flag `polling`; bila siklus sebelumnya belum selesai (Proxmox lambat), LEWATI siklus berikutnya. Jangan biarkan request menumpuk.
- **Pakai endpoint cache-ringan.** `GET /cluster/resources` dan `GET /nodes/{n}/status` dilayani dari cache `pvestatd` — murah. Hindari query berat per-guest berulang (mis. `/config`, `/rrddata`) di loop; ambil on-demand saat modal dibuka saja.
- **Skip node offline.** Jangan panggil `/nodes/{n}/status` untuk node yang `status != online`.
- **Interval wajar.** 5 dtk cukup untuk status realtime; jangan < 2 dtk. Sediakan `POLL_INTERVAL` yang bisa dinaikkan.
- **RRD, bukan sampling sendiri.** Untuk grafik histori pakai `/nodes/{n}/{type}/{vmid}/rrddata?timeframe=hour|day|...` — Proxmox sudah menyimpan RRD; jangan bikin sampler sendiri. Satu response RRD sudah membawa `cpu`, `mem`/`maxmem`, `netin`/`netout` (bytes/s), dan `diskread`/`diskwrite` (bytes/s) — cukup untuk grafik CPU+RAM+Network+Disk I/O sekaligus tanpa call tambahan.
- **IP address guest tanpa beban:** LXC → parse `ip=` dari field `net0..netN` di `/config` (lewati `dhcp`/`manual`, ambil sebelum `/CIDR`). QEMU → `/nodes/{n}/qemu/{vmid}/agent/network-get-interfaces` (butuh qemu-guest-agent aktif; bila tidak, tangani sebagai 'IP: -', bukan error). Cache di client (TTL ~60s) supaya tak fetch tiap render.
- **Copy/paste noVNC:** Copy — dengarkan event `clipboard` pd RFB (server kirim `e.detail.text` saat user seleksi teks di layar VNC), simpan, tulis ke `navigator.clipboard.writeText`. Paste — `rfb.clipboardPasteFrom(text)` + fallback ketik char-by-char.
- **Console CT = xterm.js + termproxy, BUKAN noVNC.** noVNC itu streaming gambar → berat, teks tak bisa diseleksi/copy. Untuk LXC pakai `POST /nodes/{node}/lxc/{vmid}/termproxy` (balikan {ticket,port,user,upid}) lalu WS ke `/nodes/{node}/lxc/{vmid}/vncwebsocket?port=&vncticket=`. Frontend xterm.js (@xterm/xterm@5.5.0/+esm, named export {Terminal}; addon-fit {FitAddon}). Protokol: handshake kirim `user:ticket\n`, resize `1:cols:rows:`, data `0:len:payload`, keepalive `2` tiap 30s. termproxy `cmd` HANYA terima whitelist (login/upgrade/ceph_install) — untuk tmux JANGAN kirim cmd array (ditolak), malah ketik perintah `tmux attach -t dash || tmux new -s dash` dari klien saat onopen. tmux = persist sejati (command hidup walau browser tutup, reconnect lanjut). Butuh tmux terpasang di CT. Copy HP: double-tap xterm selalu blok 1 baris penuh & tak bisa atur; metode tap-titik pakai `term._core._renderService.dimensions` RAPUH (sering null) → pakai mode "Pilih" TAHAN-GESER (drag) dgn geometri sederhana: lebar sel = (rect.width-2*PAD)/term.cols, tinggi = /term.rows; touchstart=anchor, touchmove=`term.select(col,row,len)`, touchend=auto-copy. Saat mode Pilih ON, set `touch-action:none` di .xterm-viewport/.xterm-screen + listener touch pakai {capture:true} & stopPropagation, agar 1-jari langsung seleksi (tanpa itu xterm rebut 1-jari utk scroll → butuh 2 jari). Copy HP fallback berlapis: clipboard API → execCommand (textarea fokusable nyata, iOS pakai Range) → overlay teks utk long-press copy nativ (selalu jalan di HTTP). Tombol navigasi HP: kirim escape seq via WS — ↑=`\x1b[A` (histori command sebelumnya), ↓=`\x1b[B`, ←=`\x1b[D`, →=`\x1b[C`, Tab=`\t`, Esc=`\x1b`, Ctrl+C=`\x03`. Copy handal HP/HTTP: coba `navigator.clipboard` (butuh secure ctx/HTTPS) → fallback `<textarea>`+`execCommand('copy')` → fallback `prompt`. Copy nativ desktop: `term.getSelection()` → clipboard (butuh secure ctx/HTTPS). VM tetap noVNC.
- **Console persist/anti-putus:** WS VNC TAK bisa hidup saat HP lock/background lama (OS bekukan tab + timeout sesi VNC Proxmox). Solusi realistis = auto-reconnect mulus: ambil tiket BARU tiap konek (buildRFB), reconnect pd event `disconnect` (kecuali user tutup modal → flag manualClose) & pd `visibilitychange` saat tab visible lagi + WS mati. Bersihkan canvas lama (`vnc_screen.innerHTML=''`) sebelum konek ulang. HINDARI RECONNECT LOOP: handler `disconnect` objek RFB LAMA ikut menembak saat teardown — pagari dgn `if (r !== rfb) return` (hanya RFB aktif yg boleh reconnect) + backoff. Utk shell yg benar2 persist lintas-putus: attach tmux/screen di dalam guest.
- **Copy/paste di HTTP (non-HTTPS):** `navigator.clipboard` DIBLOKIR browser di konteks tak-aman (mis. akses via IP:port HTTP) — cek `window.isSecureContext`, fallback ke `window.prompt`. Copy noVNC juga cuma terisi kalau server VNC kirim event `clipboard` saat user seleksi teks; konsol CT/LXC (xterm) sering TAK mengirimnya — Copy andal hanya di VM grafis, utk CT sarankan tmux.
- **Console responsif vs soft-keyboard:** modal tinggi tetap (mis. 82vh) akan tertutup keyboard. Pakai `window.visualViewport`: pada event `resize`/`scroll`, set tinggi container = `vv.height`, PIN overlay `fixed` ke `top=vv.offsetTop` (kalau tidak, fokus input men-scroll modal keluar layar). Fokus input tersembunyi dgn `focus({preventScroll:true})` + `body.overflow=hidden` selama console buka. Paksa noVNC re-scale (`rfb.scaleViewport = rfb.scaleViewport`). Lepas listener, restore body.overflow, `rfb.disconnect()` saat modal ditutup (MutationObserver pada #modalRoot).
- **Keyboard mobile di noVNC:** canvas TIDAK memicu soft-keyboard HP. Sediakan `<input>` tersembunyi (di dalam viewport, opacity:0, 1px — JANGAN `left:-9999px` karena sebagian browser tak buka keyboard utk elemen off-screen); tombol ⌨ dan `touchend` layar memanggil `input.focus()`. Teruskan karakter via event `input` (soft-keyboard sering tak kirim keydown per-char): loop `value`, `rfb.sendKey(codepoint)`, lalu kosongkan value. Tombol khusus (Enter=0xff0d, Backspace=0xff08, Tab=0xff09, Esc=0xff1b, panah 0xff51-54) via `keydown` pakai keysym X11.
- **noVNC import di browser:** JANGAN `import()` dari `.../lib/rfb.js` mentah — itu CommonJS/multi-file, browser lempar `exports is not defined`. Pakai bundle ESM tunggal jsdelivr: `import('https://cdn.jsdelivr.net/npm/@novnc/novnc@1.5.0/lib/rfb.js/+esm')` (path `core/rfb.js/+esm` 404; yang benar `lib/rfb.js/+esm`), ambil `{ default: RFB }`. Pastikan CSP `script-src` mengizinkan cdn.jsdelivr.net.
- **VNC/console:** proxy WebSocket biner hanya hidup selama console dibuka; tutup kedua sisi saat selesai. Ticket VNC dikirim ke noVNC sebagai password RFB; port+vncticket dari `POST .../vncproxy` harus dipakai apa adanya (jangan regenerate ticket beda dgn port). Console berlaku untuk LXC DAN QEMU (`vncproxy websocket=1` jalan di keduanya) — jangan batasi tombol console ke `type==qemu` saja. Untuk paste ke terminal via noVNC: panggil `rfb.clipboardPasteFrom(text)` lalu ketik manual char-by-char (`rfb.sendKey(codepoint,null,true/false)`) sebagai fallback lintas-OS; sediakan juga `rfb.sendCtrlAltDel()` dan toggle `scaleViewport`/`clipViewport` untuk Fit vs 1:1.
- **Terminal shell NODE (host Proxmox):** `POST /nodes/{node}/termproxy` TANPA vmid → {ticket,port,user}; WS ke `/nodes/{node}/vncwebsocket?port=&vncticket=` (URL node-level, tanpa `/lxc/{vmid}`). Reuse fungsi openTerminal(id,name,{isNode:true,node}) — cabang path tiket (`/nodes/{node}/termticket` vs `/guests/{vmid}/termticket`) & query WS (`node=` vs `vmid=`). Proxy WS backend: bila ada `node` param & tanpa `vmid`, set type='node', jangan cari di clusterResources.
- **Edit IP/gateway guest:** LXC → PUT config `netN` string (`name=eth0,bridge=,ip=CIDR,gw=`); pertahankan field lain, timpa `ip=`/`gw=` saja, langsung aktif (reboot bila belum berubah di dalam). QEMU → PUT `ipconfigN` (cloud-init), butuh reboot + template cloud-init. Validasi CIDR IPv4 (`^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$`) & gateway IPv4 SEBELUM panggil Proxmox (hemat call, tolak input buruk awal). Bersihkan cache IP client setelah edit.
- **Prompt interaktif dalam skrip `curl|bash` HARUS baca `/dev/tty`, bukan stdin.** Saat installer dijalankan `bash <(curl ...)`, stdin = skrip itu sendiri (bukan TTY), jadi `[[ -t 0 ]]` gagal & `read` menyedot isi skrip. Solusi: guard `[[ -e /dev/tty ]] && { : >/dev/tty; } 2>/dev/null`, lalu `printf ... > /dev/tty` dan `read -r var < /dev/tty` (password: `read -rs`). Terbukti menerima input user meski stdin dipipe. Sediakan juga jalur non-interaktif via env (DASH_USER/DASH_PASS).
- **Create CT/VM via API token butuh role priv lengkap**: `VM.Allocate Datastore.AllocateSpace VM.Config.* SDN.Use` (SDN.Use wajib bila bridge=VNet SDN) + `Sys.Console` (Terminal Node) + `Sys.Audit Datastore.Audit VM.Audit VM.Console VM.PowerMgmt VM.Snapshot VM.Clone VM.Migrate`. Token `--privsep 1` perlu `pveum aclmod / -token 'user@realm!name' -role X` (ACL ke token, bukan cuma user).
- **Guard konfirmasi aksi destruktif dashboard**: shutdown/reboot/reset/stop WAJIB `confirm()` per-aksi dgn pesan risiko (reset/stop = tidak graceful, risiko korup). Pakai map `ACTION_CONFIRM[act]` di `doAction`, jangan cuma guard `stop`.
- **Tema “cerah” = TERANG (light), bukan sekадар ganti aksen.** Bila user minta tema cerah, remap juga skala netral `slate` (bg-slate-950/900/800/700 → putih/abu terang, text-slate-100/400/500 → gelap, border ikut) via `html[data-theme]`, BUKAN cuma orange→hijau. KECUALIKAN `bg-black` (layar terminal/VNC) & `text-white` (toast) agar tetap terbaca. Cek sebaran netral: `grep -ohE '(bg|text|border|hover:bg)-(slate|black|white)-?[0-9]*(/[0-9]+)?' public/*.html public/*.js|sort|uniq -c`.
- **Ganti tema warna zero-risk = remap CSS via `data-theme`, JANGAN ganti class di JS.** Warna aksen Tailwind CDN (`bg-orange-600`, `text-sky-400`, dst) tersebar di puluhan titik HTML+JS. Untuk tema baru: set/hapus `<html data-theme="green">` dari JS, lalu di style.css tulis `html[data-theme="green"] .bg-orange-600 { background:var(--p-600) !important }` HANYA utk utility yg benar2 dipakai (list via `grep -ohE '(bg|text|border|hover:bg|focus:border)-(orange|sky)-[0-9]+(/[0-9]+)?' public/*.html public/*.js|sort -u`). Tema lama tanpa atribut = fallback otomatis. Persist di `localStorage`. Nol perubahan class = nol regresi. Ingat escape `/` di opacity utility jadi `.bg-orange-500\/20`.
- **Header mobile Proxmox dashboard**: sisakan aksi utama (+VM/+CT) terlihat, buang tombol sekunder (logout/ganti-pw/node/tema) ke dropdown `#menuDrop` yg dibuka `#btnMenu` (⋮) — tutup on outside-click/Esc/pilih item. Tombol berjejar horizontal meluber di HP.
- **CLI set-password interaktif = solusi anti-drama copy-paste hash.** Sediakan `scripts/set-password.mjs` + `npm run set-password`: user mengetik password di prompt (masking `*` via override `rl._writeToOutput` HANYA saat `process.stdin.isTTY`; non-TTY skip masking), skrip meng-hash scrypt & menulis `DASHBOARD_USER`+`DASHBOARD_PASSWORD_HASH` ke `.env` sendiri (filter `startsWith`, buang plaintext lama). Pakai SATU interface readline utk seluruh sesi (bikin >1 lalu close = tutup stdin pipe, prompt berikут gagal senyap). Uji di terminal via `pty.fork()` (pipe `printf|node` tak realistis utk readline). Jauh lebih andal daripada menyuruh user tempel `node -e '...' >> .env`.
- **Harden rate-limit di SEMUA endpoint verifikasi password**, termasuk `change-password` (bukan cuma login) — sesi curian bisa brute-force password lama. `loginLimiter.fail(ip)` saat password lama salah, `reset(ip)` saat sukses.
- **Jangan percaya `X-Forwarded-For`/`X-Forwarded-Proto` tanpa syarat.** Gate di balik `TRUST_PROXY=true` (default false): tanpa proxy tepercaya, attacker memalsukan XFF utk menembus rate-limit per-IP & memalsukan HTTPS pd flag Secure cookie. `TRUST_PROXY=true` hanya bila di belakang Cloudflare Tunnel/reverse-proxy.
- **Node shell auto-tmux JANGAN diaktifkan:** shell node host masih di prompt `login:`/`Password:` saat WS terbuka; auto-ketik `tmux attach` menabrak & bertumpuk. Set `tmux = useTmux && !isNode` — tmux hanya untuk guest CT (yang langsung dapat shell via ticket).
- **Cache-bust JS:** append `?v=N` ke `<script src>` tiap rilis; browser HP agresif cache app.js/features.js → fitur/tombol baru (mis. Logout) tak muncul tanpa ini.
- **User menempel snippet HARFIAH — jangan pakai placeholder terpotong.** Beri hash/token/nilai LENGKAP satu baris utuh; contoh disingkat seperti `scrypt...9b5` atau `xxx` akan disalin apa adanya ke `.env` lalu login gagal (hash rusak/terpotong). Kalau nilai panjang, sediakan perintah generate yang mencetak DAN menulis sendiri ke `.env` (mis. `node -e '...' >> .env`), bukan minta user menyalin-tempel manual. Bila update `.env` lewat shell tempel gagal berulang: JANGAN andalkan blok multi-baris ber-nested-quote atau command substitution `$(...)` — paste HP/terminal sering mengubah kutip jadi “smart quote” atau memutus di prompt `>`, sehingga `$(cat file)` masuk `.env` HARFIAH atau syntax error. Jalur paling anti-gagal: tulis skrip `.mjs` via heredoc `<<'EOF'` (kutip tunggal = tanpa ekspansi shell), baca input dari file, dan biarkan Node menulis `.env` sendiri (filter baris lama pakai `l.startsWith(...)`, bukan regex). Selalu verifikasi hasil dengan `curl -s -o /dev/null -w '%{http_code}' POST /api/auth/login` (200/401) sebelum menyuruh user coba di browser.
- **Ganti password login dari dashboard (tanpa restart):** endpoint `POST /api/auth/change-password` (butuh sesi aktif) verifikasi password lama via `verifyPassword`, tulis `DASHBOARD_PASSWORD_HASH` baru ke `.env` (hapus baris `DASHBOARD_PASSWORD=` plaintext agar tak bentrok), lalu update `storedHash` in-memory (jadikan `let`, bukan `const`) supaya berlaku instan. Tombol 🔑 di header tampil saat `loginEnabled`.
- **`DASHBOARD_PASSWORD` vs `DASHBOARD_PASSWORD_HASH`:** plaintext MASUK ke `DASHBOARD_PASSWORD` (server hash saat boot). Hash `scrypt$...` siap-pakai MASUK ke `DASHBOARD_PASSWORD_HASH`. Menaruh hash di `DASHBOARD_PASSWORD` = server meng-hash-ulang si hash → tak pernah cocok (penyebab umum "password benar tapi login gagal"). Edit `.env` WAJIB diikuti `systemctl restart` — tak dibaca ulang otomatis.
- **Footprint kecil:** proses Node tunggal, tanpa DB, ± 50–70 MB RAM — muat di LXC 1 vCPU/512 MB.

## Keamanan: hardening dashboard Proxmox

Dashboard Proxmox = target bernilai tinggi (bisa hapus/kontrol semua VM). Wajib:

- **Escape SEMUA data dari Proxmox sebelum masuk `innerHTML`.** Nama VM/CT, nama & deskripsi snapshot, volid, storage, nama node — semuanya bisa diisi attacker (mis. VM bernama `<img src=x onerror=...>`) dan jadi **stored XSS** di browser admin. Sediakan `esc()` (ganti `& < > " '`) dan terapkan di setiap interpolasi template, termasuk atribut `data-*` dan `value="..."`. Lebih baik lagi pakai `textContent`.
- **CSP sebagai lapis kedua.** Kirim header `Content-Security-Policy` (batasi `script-src`/`object-src 'none'`/`frame-ancestors 'none'`), plus `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, dan `app.disable('x-powered-by')`.
- **Bandingkan token dengan `crypto.timingSafeEqual`**, bukan `===` (cegah timing attack). Samakan panjang buffer dulu, karena timingSafeEqual melempar bila panjang beda.
- **Validasi input yang masuk path/param API Proxmox.** `vmid` harus `^\d+$`; nama snapshot `^[A-Za-z][\w-]{0,39}$`; node target migrasi harus cocok dengan daftar node nyata (`GET /nodes`). Cegah path/parameter injection dan aksi ke node fiktif.
- **Batasi ukuran body** (`express.json({ limit: '256kb' })`) dan jangan bocorkan stack trace ke client (log `e.message` saja).
- **`.env` di `.gitignore`**, tidak pernah ter-commit (verifikasi remote 404). Token API Proxmox = rahasia; jangan pernah lewat chat/riwayat.
- Verifikasi cepat: `npm audit --omit=dev` (0 vuln), lalu `curl -D-` cek header keamanan + uji 401 tanpa/salah token.
- **Login form aman tanpa dependency (zero-dep):** hash password `crypto.scryptSync` (salt 16-byte acak, N=16384, simpan `scrypt$N$salt$hash`); verifikasi `timingSafeEqual` (samakan panjang buffer dulu). JANGAN simpan plaintext. Sesi = cookie `HttpOnly; SameSite=Strict; Secure(bila https); Max-Age` berisi `base64url(payload{u,iat,exp}).HMAC-SHA256(payload,secret)` — verify HMAC timing-safe + cek `exp`. SESSION_SECRET dari env atau auto-generate ke file `.session-secret` (mode 0600, WAJIB gitignore). Rate-limit login per-IP (in-memory Map, lock setelah ~8 gagal/15 mnt). authGuard: cek sesi cookie dulu, fallback token header legacy. checkWsAuth WS upgrade: parse cookie dari `req.headers.cookie` (WS bawa cookie otomatis), verify sesi — jadi tak perlu token di query string. Endpoint `/api/auth/{status,login,logout}` di LUAR authGuard. Password plaintext boleh di `.env` (di-hash sekali saat boot) ATAU sediakan DASHBOARD_PASSWORD_HASH siap-pakai.

## Installer LXC paste-ready (curl | bash tanpa drama error)

Untuk installer yang ditempel langsung di shell CT (`bash <(curl -fsSL .../install.sh)`) dan harus jalan mulus dari nol:

- **Tanam default `REPO_URL` di script** (`REPO_URL="${REPO_URL:-https://github.com/OWNER/repo.git}"`) supaya one-liner `curl | bash` langsung meng-clone repo yang benar tanpa mengharuskan user set env. `bash <(curl ...)` menjalankan script dari proses sementara — `BASH_SOURCE` bukan direktori repo, jadi alur WAJIB fallback ke `git clone`.
- **Guard penyalinan sumber==tujuan.** Bila script di-clone langsung ke direktori tujuan (mis. `/opt/app`) lalu dijalankan dari sana, `cp -r src src` gagal `cp: 'src' and 'src' are the same file` dan dengan `set -e` installer mati total. Cek `[[ "$SRC_DIR" -ef "$APP_DIR" ]]` (bandingkan inode, tahan symlink) dan LEWATI penyalinan; untuk kasus beda-direktori pakai `cp -rT src dst` (idempotent, tak bikin `dst/src`).
- **`set -Eeuo pipefail` + `trap ... ERR` yang menampilkan `$LINENO` dan `$BASH_COMMAND`.** Tanpa trap, kegagalan di tengah pipe apt/npm tampak senyap; user butuh tahu baris & perintah penyebab.
- **Deteksi Node andal saat Node absen.** `node -v | grep -oP '\d+'` menghasilkan string KOSONG bila `node` belum ada; `[[ "$v" -lt 18 ]]` atas string kosong bisa salah-skip. Set flag `need_node=1` default, dan hanya nol-kan bila `command -v node` ada DAN versi >= 18.
- **`npm ci` bila ada `package-lock.json`** (deterministik & cepat), fallback `npm install`. Selalu `--omit=dev --no-audit --no-fund`.
- **`export LC_ALL=C.UTF-8 LANG=C.UTF-8` di awal** — image CT minimal sering tak punya `en_US.UTF-8`, memicu warning `perl: Setting locale failed` di setiap apt/nodesource. `C.UTF-8` selalu ada di Debian/Ubuntu. Terapkan juga di dalam blok `pct exec ... bash -c`.
- **Ringkasan akhir yang informatif:** cetak direktori, versi Node/npm, nama service, port (parse dari `.env`), URL (`hostname -I`), dan STATUS eksplisit BERJALAN/BELUM JALAN. Auto-start service hanya bila `.env` sudah terisi (bukan masih template placeholder) — deteksi via grep nilai placeholder.
- **systemd hardening unit:** `NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome`, `ReadWritePaths=$APP_DIR`, `PrivateTmp`, `User=` service-account non-login, `ExecStart=$(command -v node) ...` (path absolut).

### update.sh — perbarui app terinstall tanpa merusak kepemilikan

App yang di-clone installer biasanya dimiliki service-account (mis. `pvedash`), tapi user update sebagai `root`. `git pull` sebagai root menimbulkan dua masalah:

- **`fatal: detected dubious ownership`** — git menolak repo yang pemiliknya beda dari pemanggil. Fix: `git config --global --add safe.directory $APP_DIR` untuk root DAN service-account.
- **File baru jadi milik root** → service (jalan sebagai service-account) gagal baca. Fix: `git pull` **sebagai pemilik repo** (`sudo -u "$OWNER" git -C "$APP_DIR" pull --ff-only`; deteksi owner via `stat -c '%U' "$APP_DIR"`), lalu `chown -R $OWNER:$OWNER $APP_DIR` jaga-jaga, baru `systemctl restart`. Sediakan `update.sh` paste-ready agar update = satu baris, bukan urutan manual yang bikin drama.
- **Reinstall dependency hanya bila perlu:** `git diff --name-only $BEFORE $AFTER | grep -q package-lock.json` sebelum `npm ci` — hindari reinstall tiap update.

### Installer TIDAK auto-start bila .env masih template

Installer sengaja membuat service `enabled` tapi tidak `start` selama `.env` belum diisi kredensial. Setelah user mengisi `.env` PERTAMA kali, service masih `inactive (dead)` sampai `systemctl start` manual. Dokumentasikan langkah eksplisit: isi `.env` → `systemctl start <service>` → `systemctl status`. `restart` atas service yang belum pernah start juga bekerja, tapi user sering lupa langkah start-nya sama sekali.

### create-ct.sh (dijalankan di host Proxmox)

- **Jangan `sleep N` buta menunggu CT boot.** Ganti dengan loop tunggu-jaringan nyata: `for i in $(seq 1 30); do pct exec $CTID -- bash -c 'getent hosts deb.nodesource.com || ping -c1 -W1 1.1.1.1' && break; sleep 2; done`. `sleep 8` bisa terlalu cepat (apt gagal resolve) atau buang waktu.
- **Validasi awal:** `command -v pct`, CTID belum dipakai (`pct status`), dan IP statis wajib disertai `GW`.
- Rapikan nama template: `pveam list` kadang balas path lengkap; ambil `${TMPL##*/}` sebelum menyusun `storage:vztmpl/nama`.

## Pitfalls

- **Self-signed SSL:** request gagal bila client verifikasi cert. Bypass di testing (`verify=False`); di produksi pasang CA benar, jangan matikan verifikasi permanen.
- **Ticket vs Token:** ticket kedaluwarsa ~2 jam dan butuh CSRF untuk mutasi — repot untuk otomasi. Pakai API token untuk script/cron.
- **Realm salah:** username wajib lengkap `user@pam`/`user@pve`. Salah realm → `401`.
- **Payload form-encoded:** banyak endpoint butuh `application/x-www-form-urlencoded`, bukan JSON. Di Node pakai `qs.stringify`; di Python kirim `data=` (bukan `json=`).
- **Async task:** aksi start/stop/clone/backup balik UPID, bukan hasil final. JANGAN anggap sukses tanpa poll task sampai `exitstatus=OK` — cek gagal senyap.
- **Hapus saat running:** Proxmox tolak DELETE VM/CT yang `running`. Stop dan tunggu `stopped` dulu.
- **Clone linked vs full:** linked clone (`full=0`) butuh template tetap ada & storage yang mendukung; untuk VM independen pakai `full=1`.
- **sshkeys encoding:** field `sshkeys` cloud-init harus URL-encoded; newline antar key jadi `%0A`. Salah encode → key tidak masuk.
- **VMID bentrok:** cek vmid belum dipakai sebelum clone/create (`GET /cluster/resources`), atau pakai `GET /cluster/nextid`.
- **Privilege token:** dengan `--privsep 1`, token butuh ACL sendiri terpisah dari user. Bila `403`, assign role ke token, bukan cuma ke user.
- **Create CT/VM `403 SDN.Use`:** PVE 8.x/9.x memeriksa privilege `SDN.Use` pada zona SDN bridge (`/sdn/zones/localnetwork/vmbrN`) saat membuat guest, terpisah dari `VM.Allocate`. Role otomasi lama (pra-SDN) tak punya ini → create gagal walau start/stop/snapshot jalan. Tambah `SDN.Use` (dan `VM.Console` untuk VNC) ke role.
- **Bar/persen CPU guest sudah ternormalisasi.** Field `cpu` dari `/cluster/resources` sudah pecahan 0–1 rata-rata SEMUA core (mis. 0.011 = 1.1% total), BUKAN per-core. Untuk persen tampilan cukup `cpu*100`; untuk lebar bar cukup `min(100, cpu*100)`. Jangan kalikan lagi dengan `maxcpu` atau ×100 kedua kali — bug klasik `pct(cpu,1)*100` membuat 1% jadi 110% dan bar mentok penuh.
- **`fetch()` Node MENGABAIKAN opsi `agent`/`dispatcher` dari `node:https`.** Bila backend pakai `fetch(url, { agent: new https.Agent({ rejectUnauthorized:false }) })`, opsi bypass cert TIDAK berlaku dan koneksi ke Proxmox self-signed gagal total dengan error samar `fetch failed` (cause `DEPTH_ZERO_SELF_SIGNED_CERT`) — sebelum auth, jadi bukan 401. Gejala khas: `curl -k` sukses tapi dashboard `fetch failed`. Perbaikan zero-dependency: pakai `https.request` (menghormati `rejectUnauthorized` penuh); atau pasang `undici` dan set dispatcher/`Agent({connect:{rejectUnauthorized:false}})`. `PVE_VERIFY_SSL=false` hanya efektif bila client HTTP-nya benar-benar menerapkan opsi tersebut.

## Verification Checklist

- [ ] `GET /version` balas 200 dengan token/ticket (auth benar, realm lengkap)
- [ ] Bypass/verifikasi SSL sesuai lingkungan (testing vs produksi)
- [ ] Setiap aksi mutasi memoll UPID sampai `exitstatus=OK`
- [ ] Provisioning: VM boot, cloud-init terpasang, SSH reachable
- [ ] Snapshot dibuat sebelum operasi destruktif; rollback teruji
- [ ] Backup tersimpan di storage & restore ke vmid baru start OK
- [ ] Delete memverifikasi status `stopped` sebelum DELETE
- [ ] Integrasi monitor: poll on-demand (idle = 0 request), guard anti-overlap, skip node offline, interval >= 5 dtk
- [ ] Keamanan dashboard: semua data Proxmox di-escape sebelum innerHTML (anti-XSS), CSP + security headers aktif, token dibanding timing-safe, input (vmid/snapshot/node) divalidasi, `.env` tak ter-commit
