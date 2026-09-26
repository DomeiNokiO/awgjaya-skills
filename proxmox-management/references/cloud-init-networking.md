# Cloud-init & Networking di Proxmox

Cloud-init hanya bekerja pada **VM template** yang dibangun dari cloud image (mis. Ubuntu/Debian cloud image), bukan ISO installer biasa.

## Membangun template cloud-init (sekali saja)

```bash
# di node Proxmox
cd /var/lib/vz/template/iso
wget https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img

qm create 9000 --name ubuntu-2404-tmpl --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0 --scsihw virtio-scsi-pci --ostype l26
qm importdisk 9000 noble-server-cloudimg-amd64.img local-lvm
qm set 9000 --scsi0 local-lvm:vm-9000-disk-0
qm set 9000 --ide2 local-lvm:cloudinit          # drive cloud-init
qm set 9000 --boot order=scsi0 --serial0 socket --vga serial0
qm set 9000 --agent enabled=1                    # qemu-guest-agent
qm disk resize 9000 scsi0 10G
qm template 9000                                 # kunci jadi template
```

## Deploy dari template

```bash
qm clone 9000 150 --name web-01 --full --storage local-lvm
qm set 150 --ciuser deploy \
  --sshkeys ~/.ssh/id_ed25519.pub \
  --ipconfig0 ip=192.168.1.150/24,gw=192.168.1.1 \
  --nameserver 1.1.1.1 --searchdomain lan \
  --memory 4096 --cores 2
qm cloudinit update 150
qm start 150
# tunggu boot, lalu: ssh deploy@192.168.1.150
```

## Opsi cloud-init penting (`qm set`)

| Opsi | Contoh | Fungsi |
|---|---|---|
| `--ciuser` | `deploy` | Username default |
| `--cipassword` | `'***'` | Password (lebih baik pakai sshkeys) |
| `--sshkeys` | `~/.ssh/id_ed25519.pub` | Public key (bisa multi-baris) |
| `--ipconfig0` | `ip=dhcp` atau `ip=192.168.1.150/24,gw=192.168.1.1` | IP NIC pertama |
| `--ipconfig0` (IPv6) | `ip6=auto` / `ip6=2001:db8::10/64,gw6=2001:db8::1` | IPv6 |
| `--nameserver` | `1.1.1.1 8.8.8.8` | DNS |
| `--searchdomain` | `lan` | Domain pencarian |
| `--ciupgrade` | `1` | apt/dnf upgrade saat boot pertama (PVE 8) |

## Networking VM

### Bridge & VLAN

```bash
qm set 150 --net0 virtio,bridge=vmbr0                 # bridge biasa
qm set 150 --net0 virtio,bridge=vmbr0,tag=10          # VLAN tag 10
qm set 150 --net0 virtio,bridge=vmbr0,rate=100        # rate limit 100 MB/s
qm set 150 --net0 virtio,bridge=vmbr0,firewall=1      # aktifkan firewall NIC
```

### Dual-NIC (mis. LAN + DMZ)

```bash
qm set 150 --net0 virtio,bridge=vmbr0 \
           --net1 virtio,bridge=vmbr1,tag=20
qm set 150 --ipconfig0 ip=192.168.1.150/24,gw=192.168.1.1 \
           --ipconfig1 ip=10.20.0.150/24
```

## Networking LXC

```bash
pct set 250 --net0 name=eth0,bridge=vmbr0,ip=dhcp
pct set 250 --net0 name=eth0,bridge=vmbr0,ip=192.168.1.250/24,gw=192.168.1.1,tag=10
pct set 250 --nameserver 1.1.1.1 --searchdomain lan
```

## Contoh netplan hasil cloud-init (dalam guest Ubuntu)

```yaml
# /etc/netplan/50-cloud-init.yaml (di-generate otomatis)
network:
  version: 2
  ethernets:
    eth0:
      addresses: [192.168.1.150/24]
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]
```

## Pitfalls networking

- **Cloud image, bukan ISO:** cloud-init tidak jalan pada VM yang diinstall dari ISO installer. Pakai `*-cloudimg-amd64.img`.
- **`qm cloudinit update` wajib** setelah mengubah opsi ci; kalau tidak, disk ci lama tetap dipakai.
- **Guest agent:** untuk `qm guest cmd`/IP discovery, install `qemu-guest-agent` di guest & `--agent enabled=1`.
- **VLAN-aware bridge:** `tag=` hanya bekerja bila `vmbr0` diset VLAN-aware di `/etc/network/interfaces` (`bridge-vlan-aware yes`).
- **MAC statis:** tambahkan `macaddr=` pada `--net0` bila butuh reservasi DHCP tetap setelah clone.
