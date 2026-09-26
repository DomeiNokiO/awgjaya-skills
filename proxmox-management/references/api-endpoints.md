# Proxmox VE API Endpoint Map

Base URL: `https://<PVE_HOST>:8006/api2/json`. Semua contoh relatif terhadap base ini.

Auth header (token): `Authorization: PVEAPIToken=USER@REALM!TOKENID=SECRET`

## Access / Auth

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/version` | Cek konektivitas & versi (uji auth) |
| POST | `/access/ticket` | Login password → ticket + CSRF |
| GET | `/access/users` | Daftar user |
| POST | `/access/users/{userid}/token/{tokenid}` | Buat API token |

## Nodes

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/nodes` | Daftar node |
| GET | `/nodes/{node}/status` | Status node (CPU/RAM/uptime) |
| GET | `/nodes/{node}/qemu` | Daftar VM di node |
| GET | `/nodes/{node}/lxc` | Daftar container di node |
| GET | `/nodes/{node}/tasks` | Riwayat task |
| GET | `/nodes/{node}/tasks/{upid}/status` | Status task (poll UPID) |

## QEMU (VM)  — `type = qemu`

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/nodes/{node}/qemu` | Buat VM (`vmid`,`name`,`memory`,`cores`,`net0`,`scsi0`,`ostype`) |
| GET | `/nodes/{node}/qemu/{vmid}/config` | Baca konfigurasi |
| PUT | `/nodes/{node}/qemu/{vmid}/config` | Ubah konfig (cloud-init, net, mem, dll) |
| GET | `/nodes/{node}/qemu/{vmid}/status/current` | Status runtime |
| POST | `/nodes/{node}/qemu/{vmid}/status/start` | Start |
| POST | `/nodes/{node}/qemu/{vmid}/status/shutdown` | Shutdown graceful |
| POST | `/nodes/{node}/qemu/{vmid}/status/stop` | Stop paksa |
| POST | `/nodes/{node}/qemu/{vmid}/status/reboot` | Reboot |
| POST | `/nodes/{node}/qemu/{vmid}/clone` | Clone (`newid`,`name`,`full`,`storage`) |
| PUT | `/nodes/{node}/qemu/{vmid}/resize` | Resize disk (`disk`,`size=+20G`) |
| POST | `/nodes/{node}/qemu/{vmid}/migrate` | Migrasi (`target`,`online`,`with-local-disks`) |
| GET/POST | `/nodes/{node}/qemu/{vmid}/snapshot` | List / buat snapshot |
| POST | `/nodes/{node}/qemu/{vmid}/snapshot/{name}/rollback` | Rollback |
| DELETE | `/nodes/{node}/qemu/{vmid}/snapshot/{name}` | Hapus snapshot |
| DELETE | `/nodes/{node}/qemu/{vmid}` | Hapus VM (`purge=1`) |

## LXC (Container) — `type = lxc`

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/nodes/{node}/lxc` | Buat CT (`vmid`,`ostemplate`,`cores`,`memory`,`rootfs`,`password`,`net0`) |
| PUT | `/nodes/{node}/lxc/{vmid}/config` | Ubah konfig |
| POST | `/nodes/{node}/lxc/{vmid}/status/{start\|shutdown\|stop}` | Lifecycle |
| POST | `/nodes/{node}/lxc/{vmid}/clone` | Clone |
| POST | `/nodes/{node}/lxc/{vmid}/resize` | Resize rootfs |
| DELETE | `/nodes/{node}/lxc/{vmid}` | Hapus CT |

## Storage

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/nodes/{node}/storage` | Daftar storage + kapasitas |
| GET | `/nodes/{node}/storage/{storage}/content` | Isi storage (ISO, template, disk, backup) |
| POST | `/nodes/{node}/storage/{storage}/download-url` | Unduh ISO/template dari URL |

## Backup / vzdump

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/nodes/{node}/vzdump` | Backup (`vmid`,`storage`,`mode=snapshot`,`compress=zstd`) |
| GET/POST | `/cluster/backup` | Daftar / buat jadwal backup |

## Cluster / HA

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/cluster/resources` | Semua resource (`--type vm`) |
| GET | `/cluster/nextid` | VMID bebas berikutnya |
| GET | `/cluster/status` | Status quorum cluster |
| GET/POST | `/cluster/ha/resources` | Resource HA |
| GET/POST | `/cluster/ha/groups` | Grup HA |

## Firewall

| Method | Endpoint | Fungsi |
|---|---|---|
| GET/POST | `/cluster/firewall/rules` | Aturan level datacenter |
| GET/POST | `/nodes/{node}/qemu/{vmid}/firewall/rules` | Aturan per-VM |
| GET/PUT | `/nodes/{node}/qemu/{vmid}/firewall/options` | Opsi firewall VM (`enable`) |

## Catatan penting

- Semua aksi mutasi (start/stop/clone/backup/migrate) mengembalikan **UPID**. Poll `/nodes/{node}/tasks/{upid}/status` sampai `status=stopped`, cek `exitstatus=OK`.
- Body POST/PUT umumnya `application/x-www-form-urlencoded`. Kirim `data=` (Python `requests`) / `qs.stringify` (Node), bukan JSON.
- Array (mis. `sshkeys` multi-baris) harus URL-encoded.
