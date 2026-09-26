# Installer LXC paste-ready untuk aplikasi Node di Proxmox

Pola installer yang ditempel langsung di CT dan jalan mulus dari nol. Distilasi dari dashboard Proxmox (Node+Express+ws). Ganti `OWNER/repo`, `APP_*`, `SERVICE`.

## Pitfall inti (yang bikin installer gagal di CT)

| Gejala | Penyebab | Fix |
|---|---|---|
| `cp: 'src' and 'src' are the same file` → installer mati (`set -e`) | script di-clone langsung ke `$APP_DIR` lalu jalan dari sana; `SRC_DIR == APP_DIR` | guard `[[ "$SRC_DIR" -ef "$APP_DIR" ]]` skip copy; else `cp -rT` |
| `curl|bash` minta REPO_URL padahal harusnya otomatis | `bash <(curl ...)` → `BASH_SOURCE` bukan repo, tak ada package.json lokal | tanam default `REPO_URL="${REPO_URL:-https://github.com/OWNER/repo.git}"`, fallback `git clone` |
| `perl: Setting locale failed` di tiap apt | image CT minimal tanpa `en_US.UTF-8` | `export LC_ALL=C.UTF-8 LANG=C.UTF-8` di awal (juga di dalam `pct exec`) |
| installer skip Node walau Node belum ada | `node -v|grep -oP '\d+'` = string kosong, `[[ "" -lt 18 ]]` salah | flag `need_node=1` default, nol-kan hanya bila `command -v node` ADA dan versi>=18 |
| apt gagal resolve tepat setelah `pct start` | `sleep 8` buta, jaringan CT belum siap | loop tunggu-jaringan nyata (getent/ping), retry 30x |

## Kerangka install.sh (di dalam CT)

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
export LC_ALL=C.UTF-8 LANG=C.UTF-8
APP_USER="appsvc"; APP_DIR="/opt/app"; SERVICE="app"; NODE_MAJOR="20"
REPO_URL="${REPO_URL:-https://github.com/OWNER/repo.git}"
trap 'echo "[ERR] gagal di baris $LINENO: ${BASH_COMMAND}" >&2' ERR
[[ $EUID -eq 0 ]] || { echo "jalankan sebagai root"; exit 1; }

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg git openssl >/dev/null

need_node=1
if command -v node >/dev/null 2>&1; then
  cur="$(node -v 2>/dev/null | grep -oP '\d+' | head -1 || echo 0)"
  [[ "${cur:-0}" -ge 18 ]] && need_node=0
fi
if [[ "$need_node" -eq 1 ]]; then
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - >/dev/null 2>&1
  apt-get install -y -qq nodejs >/dev/null
fi

id "$APP_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$SRC_DIR/package.json" ]]; then
  rm -rf "$APP_DIR"; git clone --depth 1 "$REPO_URL" "$APP_DIR"; SRC_DIR="$APP_DIR"
fi
mkdir -p "$APP_DIR"
if [[ "$SRC_DIR" -ef "$APP_DIR" ]]; then
  :  # sudah di tujuan, tak perlu salin
else
  cp -rT "$SRC_DIR/src" "$APP_DIR/src"
  cp -rT "$SRC_DIR/public" "$APP_DIR/public"
  cp -f "$SRC_DIR/package.json" "$APP_DIR/"
  [[ -f "$SRC_DIR/package-lock.json" ]] && cp -f "$SRC_DIR/package-lock.json" "$APP_DIR/"
fi
cd "$APP_DIR"
if [[ -f package-lock.json ]]; then npm ci --omit=dev --no-audit --no-fund; else npm install --omit=dev --no-audit --no-fund; fi
[[ -f .env ]] || cp .env.example .env
chown -R "$APP_USER:$APP_USER" "$APP_DIR"; chmod 640 .env

cat > "/etc/systemd/system/${SERVICE}.service" <<EOF
[Unit]
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=$(command -v node) ${APP_DIR}/src/server.js
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${APP_DIR}
PrivateTmp=true
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload; systemctl enable "$SERVICE" >/dev/null 2>&1
# auto-start hanya bila .env sudah diisi (bukan placeholder)
grep -q 'SECRET=xxxx' .env || systemctl restart "$SERVICE"
```

## Tunggu-jaringan CT (create-ct.sh, di host Proxmox)

```bash
pct start "$CTID"
for i in $(seq 1 30); do
  pct exec "$CTID" -- bash -c 'getent hosts deb.nodesource.com >/dev/null 2>&1 || ping -c1 -W1 1.1.1.1 >/dev/null 2>&1' && break
  sleep 2
done
pct exec "$CTID" -- bash -c "set -Eeuo pipefail; export DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8 LANG=C.UTF-8; apt-get update -qq; apt-get install -y -qq curl git ca-certificates gnupg openssl >/dev/null; rm -rf /opt/app; git clone --depth 1 '$REPO_URL' /opt/app; cd /opt/app; bash scripts/install.sh"
```

## Verifikasi

- `bash -n install.sh create-ct.sh` (syntax) sebelum commit.
- Uji guard cp: buat dir dgn `src/`, set `SRC_DIR=APP_DIR`, pastikan branch skip terpakai (tak ada error same-file).
- Uji `cp -rT` idempotent: jalankan 2x, exit 0, isi tidak dobel.
- Uji `npm ci` dgn lockfile di sandbox non-root sebelum menaruh di CT.
