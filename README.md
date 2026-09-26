# awgjaya-skills

Kumpulan skill kustom untuk **Hermes Agent**. Tiap folder di root repo ini adalah satu skill (berisi `SKILL.md` + folder `references/` bila ada).

## Daftar skill

| Skill | Fungsi |
|-------|--------|
| [`anti-ai-slop`](./anti-ai-slop) | Filter gaya agar teks & UI tidak terbaca "AI-generated". Doktrin tulisan + UI, daftar kata/frasa terlarang, tell bahasa Indonesia, 38 aturan UI, sistem warna OKLCH, tipografi, scoring anti-slop. |

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
└── anti-ai-slop/
    ├── SKILL.md
    └── references/
        ├── writing-banned.md
        ├── indonesian-tells.md
        ├── ui-rules.md
        └── ui-deep.md
```

## Lisensi & sumber

`anti-ai-slop` disaring & dikonsolidasikan dari beberapa repo publik: jalaalrd/anti-ai-slop-writing, dharmawan-id/anti-ai-slop, miqdadbadjuber/anti-slop, Nutlope/hallmark, dtransla-maker/Anti-AI-Design-Slop, prodigeproject/prodigeui. Gunakan sesuai lisensi masing-masing sumber.
