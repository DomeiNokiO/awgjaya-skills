# awgjaya-skills

Kumpulan skill kustom untuk **Hermes Agent**. Tiap folder di root repo ini adalah satu skill (berisi `SKILL.md` + folder `references/` bila ada).

## Daftar skill

| Skill | Fungsi |
|-------|--------|
| [`anti-ai-slop`](./anti-ai-slop) | Filter gaya agar teks & UI tidak terbaca "AI-generated". Doktrin tulisan + UI, daftar kata/frasa terlarang, tell bahasa Indonesia, 38 aturan UI, sistem warna OKLCH, tipografi, scoring anti-slop. |
| [`pentest-playbook`](./pentest-playbook) | Metodologi pentest **authorized-only**: 7 fase (passive recon → evidence report), gate otorisasi wajib, pivot triggers, laporan evidence-first. Referensi per-domain (web/API/cloud), tool map Kali per fase, dan template laporan. Bukan payload/eksploit — panduan alur & routing. |
| [`proxmox-management`](./proxmox-management) | Kelola VM, container (CT/LXC), dan integrasi API Proxmox VE. Buat kebutuhan homelab/hosting Proxmox. |
| [`secure-laravel-delivery`](./secure-laravel-delivery) | Deliver aplikasi Laravel ke GitHub + host VPS dengan aman: hardening, deploy, env. |
| [`reddit-reading`](./reddit-reading) | Baca Reddit (subreddit, search, thread, user) via API JSON, tanpa browser. |
| [`rss-feeds`](./rss-feeds) | Baca feed RSS/Atom/JSON dan temukan feed di balik sebuah halaman. |

## Cara pasang ke Hermes Agent lain

Skill dibaca dari direktori skills profil aktif, biasanya `~/.hermes/skills/` atau `/opt/data/skills/` (tergantung setup). Salin folder skill ke dalam salah satu **kategori** di situ (mis. `creative/`).

**Cara 1 — clone lalu salin:**
```bash
git clone https://github.com/DomeiNokiO/awgjaya-skills.git
# ganti <SKILLS_DIR> dengan direktori skills Hermes kamu (mis. ~/.hermes/skills)
mkdir -p <SKILLS_DIR>/creative
cp -r awgjaya-skills/anti-ai-slop <SKILLS_DIR>/creative/
```

**Cara 2 — satu skill saja (sparse):**
```bash
cp -r awgjaya-skills/anti-ai-slop /path/ke/skills/creative/
```

Setelah disalin, skill langsung terbaca oleh agent (auto-load saat trigger-nya cocok — lihat `description` di frontmatter tiap `SKILL.md`). Tidak perlu restart pada kebanyakan setup; kalau tidak muncul, mulai sesi baru.

## Struktur

```
awgjaya-skills/
├── anti-ai-slop/
│   ├── SKILL.md
│   └── references/
│       ├── writing-banned.md
│       ├── indonesian-tells.md
│       ├── ui-rules.md
│       └── ui-deep.md
└── pentest-playbook/
    ├── SKILL.md
    ├── references/
    │   ├── web-app.md
    │   ├── api.md
    │   ├── cloud.md
    │   └── tooling.md
    └── templates/
        └── report.md
```

## Lisensi & sumber

`anti-ai-slop` disaring & dikonsolidasikan dari beberapa repo publik: jalaalrd/anti-ai-slop-writing, dharmawan-id/anti-ai-slop, miqdadbadjuber/anti-slop, Nutlope/hallmark, dtransla-maker/Anti-AI-Design-Slop, prodigeproject/prodigeui. Gunakan sesuai lisensi masing-masing sumber.

`reddit-reading` & `rss-feeds` oleh Teknium/Hermes Agent (MIT). `proxmox-management`, `pentest-playbook`, `secure-laravel-delivery` disusun untuk kebutuhan sendiri (MIT).

### Tidak disertakan (sengaja)

- **`kali-pentest`** (~1.9 MB, 309 file) dan **`hack-skills`** (102 sub-skill) — paket pihak ketiga berlisensi MIT (© VillanCh). Bukan buatan sendiri; ukurannya besar dan sudah punya repo upstream masing-masing. Ambil langsung dari sumber aslinya, bukan dari sini.
- **Prompt jailbreak** ("GODMODE / Zero Refusal" dan sejenisnya) — bukan skill; dikecualikan permanen.
