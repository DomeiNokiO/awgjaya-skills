# Proxmox CLI Cheatsheet

Jalankan di node Proxmox (via SSH) melalui `terminal`. `qm`=QEMU/VM, `pct`=LXC, `pvesh`=API shell, `pvesm`=storage, `pveum`=user/token, `vzdump`=backup.

## Inventaris & status

```bash
qm list                                  # VM di node ini
pct list                                 # container di node ini
pvesh get /cluster/resources --type vm   # semua VM/CT cluster
pvesh get /nodes                         # daftar node
pvesh get /cluster/nextid                # VMID bebas berikutnya
qm status 100 ; qm config 100            # status & konfig VM
pct status 200 ; pct config 200          # status & konfig CT
```

## Lifecycle

```bash
qm start 100 ; qm shutdown 100 ; qm stop 100 ; qm reboot 100 ; qm reset 100
pct start 200 ; pct shutdown 200 ; pct stop 200
qm suspend 100 ; qm resume 100           # pause/resume
```

## Buat VM manual

```bash
qm create 130 --name test --memory 2048 --cores 2 --net0 virtio,bridge=vmbr0 \
  --scsihw virtio-scsi-pci --scsi0 local-lvm:20 --ostype l26 --ide2 local:iso/ubuntu.iso,media=cdrom \
  --boot order=scsi0;ide2
```

## Buat container LXC

```bash
pveam update && pveam available | grep ubuntu
pveam download local ubuntu-24.04-standard_24.04-2_amd64.tar.zst
pct create 210 local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
  --hostname app-ct --cores 2 --memory 2048 --rootfs local-lvm:8 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp --password --unprivileged 1 --features nesting=1
```

## Clone & template

```bash
qm template 9000                         # jadikan VM 9000 template
qm clone 9000 150 --name web-01 --full --storage local-lvm
pct clone 210 250 --hostname app-clone --full
```

## Cloud-init (VM)

```bash
qm set 150 --ciuser deploy --sshkeys ~/.ssh/id_ed25519.pub
qm set 150 --ipconfig0 ip=192.168.1.150/24,gw=192.168.1.1
qm set 150 --nameserver 1.1.1.1 --searchdomain lan
qm set 150 --ciupgrade 1                 # apt upgrade saat boot pertama
qm cloudinit update 150                  # regenerate disk cloud-init
qm cloudinit dump 150 user               # inspeksi user-data
```

## Resource & disk

```bash
qm set 150 --memory 4096 --cores 4
qm resize 150 scsi0 +20G                 # perbesar disk (tidak bisa mengecil)
qm set 150 --net0 virtio,bridge=vmbr0,tag=10   # VLAN 10
qm disk move 150 scsi0 local-lvm --delete       # pindah storage disk
pct set 250 --memory 4096 ; pct resize 250 rootfs +10G
```

## Snapshot

```bash
qm listsnapshot 150
qm snapshot 150 pre-deploy --description "before deploy" --vmstate 1
qm rollback 150 pre-deploy
qm delsnapshot 150 pre-deploy
pct snapshot 250 pre ; pct rollback 250 pre ; pct delsnapshot 250 pre
```

## Backup & restore (vzdump)

```bash
vzdump 150 --storage local --mode snapshot --compress zstd --notes-template '{{guestname}}'
vzdump 150 200 250 --storage backup-nfs --mode snapshot   # beberapa sekaligus
vzdump --all 1 --storage backup-nfs --mode snapshot        # semua guest
qmrestore /var/lib/vz/dump/vzdump-qemu-150-*.vma.zst 151 --storage local-lvm
pct restore 251 /var/lib/vz/dump/vzdump-lxc-250-*.tar.zst --storage local-lvm
```

## Migrasi

```bash
qm migrate 150 node2 --online --with-local-disks     # live migrate
pct migrate 250 node2 --restart                       # CT butuh restart
```

## Storage

```bash
pvesm status                             # kapasitas semua storage
pvesm list local                         # isi storage
pvesm alloc local-lvm 150 vm-150-disk-1 10G
```

## User, role, token

```bash
pveum user add automation@pve
pveum role add Automational -privs "VM.Allocate VM.Config.Disk VM.PowerMgmt VM.Clone VM.Snapshot VM.Audit Datastore.AllocateSpace Datastore.Audit"
pveum aclmod / -user automation@pve -role Automational
pveum user token add automation@pve automate --privsep 0
pveum user token list automation@pve
```

## Firewall

```bash
pve-firewall status
pve-firewall compile                     # cek aturan tanpa apply
qm set 150 --firewall 1
```

## Console & guest agent

```bash
qm terminal 150                          # serial console
qm guest cmd 150 network-get-interfaces  # butuh qemu-guest-agent
qm agent 150 ping
```
