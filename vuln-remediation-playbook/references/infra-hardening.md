# Infrastruktur & Hardening — Tambalan per Kelas

Aturan inti: **least privilege + kurangi attack surface + patch.** Batasi blast-radius saat satu lapis jebol.

## Linux Privilege Escalation
**Akar umum:** SUID binary berlebih, sudo misconfig, cron world-writable, kernel usang, creds di disk.
**Tambal:**
- Hapus SUID/SGID tak perlu: `find / -perm -4000` → audit, cabut yang tak wajib.
- `sudoers`: hindari `NOPASSWD` luas, `ALL`, wildcard yang bisa disalahgunakan; jangan izinkan editor/interpreter via sudo.
- File/skrip yang dijalankan root TIDAK boleh writable oleh user lain; cek PATH cron.
- Patch kernel & paket rutin (dirtypipe/pwnkit dsb).
- Jangan simpan password/token di file world-readable; `chmod 600`, pakai secret manager.
- Hardening: `noexec,nosuid,nodev` pada mount yang cocok; AppArmor/SELinux enforce.

## Windows Privilege Escalation
**Tambal:** tutup unquoted service path; ACL service/registry writable diperketat; `AlwaysInstallElevated` off; hapus cached creds; token privileges dibatasi; patch (PrintNightmare dsb); LAPS untuk password admin lokal unik.

## Active Directory (ACL abuse, Kerberos, ADCS, NTLM relay)
**Tambal:**
- **Kerberos:** akun service pakai gMSA (password panjang acak, rotasi otomatis) → matikan kerberoasting; matikan `DES`/RC4; batasi delegation (hapus unconstrained, pakai constrained/RBCD terkontrol); AS-REP: aktifkan preauth.
- **ACL:** audit & cabut hak berbahaya (`GenericAll`/`WriteDacl`/`WriteOwner`) pada objek/OU sensitif; tiering admin (T0/T1/T2, jangan login DA di workstation).
- **ADCS:** perbaiki template rentan (ESC1-8): matikan `ENROLLEE_SUPPLIES_SUBJECT`, batasi enroll, enforce manager approval; enable `EKU`/SAN validation.
- **NTLM relay:** aktifkan SMB signing (enforce), LDAP signing + channel binding (EPA), matikan NTLM di mana bisa, `WebClient` off, `MIC`/EPA aktif.

## Container / Kubernetes Escape
**Tambal:**
- Container non-root (`USER`), `readOnlyRootFilesystem`, drop semua caps (`cap_drop: [ALL]`), `no-new-privileges`, seccomp/AppArmor profile.
- JANGAN `privileged: true`, jangan mount `docker.sock`, jangan hostPath sensitif, jangan hostPID/hostNetwork tanpa alasan.
- K8s: RBAC least-privilege (bukan cluster-admin ke SA), NetworkPolicy default-deny, PodSecurity `restricted`, secret via secret store bukan env plaintext, matikan auto-mount SA token bila tak perlu.

## Lateral Movement (Linux/Windows)
**Tambal:** segmentasi jaringan (blok SMB/RDP/WinRM antar-workstation), unique local admin creds (LAPS), matikan reuse password, monitor auth anomali, disable protokol legacy (SMBv1, LLMNR/NBT-NS/mDNS → cegah poisoning).

## Exposed / Unauthorized Services
**Tambal:** jangan ekspos service internal ke publik (bind ke localhost/VPN); ganti default cred; auth wajib di Redis/Mongo/Elasticsearch/Docker API/K8s API; firewall default-deny inbound; matikan service tak dipakai.

## Network / TLS
**Tambal:** TLS 1.2+ (matikan SSLv3/TLS1.0/1.1), cipher kuat, HSTS, verifikasi sertifikat (jangan `verify=false` di produksi — lihat proxmox-management), sertifikat valid (bukan self-signed di internet). Segmentasi & firewall egress juga (batasi SSRF/exfil).

## Secrets Management
**Tambal:** secret TAK pernah di kode/git (scan history, rotasi bila bocor); `.env` di `.gitignore`; pakai vault/secret manager atau env di runtime; file secret `chmod 600`; rotasi berkala; least-privilege token (scope minimal, expiry).

## Dependency Confusion / Supply Chain
**Tambal:** pin registry + scope paket internal (`@scope`), konfigurasi `.npmrc`/`pip.conf` agar paket internal hanya dari registri privat; lockfile + integrity hash (`package-lock`, `--require-hashes`); verifikasi signature; SCA/`npm audit`/dependabot; jangan auto-install dari sumber tak dikenal; review paket baru.

## Verifikasi umum infra
1. Ulang teknik privesc/escape PoC → gagal (hak tak cukup / jalur tertutup).
2. `find SUID`, audit sudoers, cek RBAC/PodSecurity → sesuai least-privilege.
3. Scan ulang port/service eksternal → hanya yang diinginkan terbuka.
4. Secret scan history → bersih.
