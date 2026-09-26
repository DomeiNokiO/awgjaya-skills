#!/usr/bin/env python3
"""
Proxmox VE CLI client (API-token based) untuk otomasi.

Auth via env:
  PVE_HOST          contoh: 192.168.1.10
  PVE_NODE          contoh: pve  (default node untuk operasi node-scoped)
  PVE_TOKEN_ID      contoh: automation@pve!automate
  PVE_TOKEN_SECRET  contoh: xxxxxxxx-xxxx-...
  PVE_VERIFY_SSL    'true' untuk verifikasi cert (default: false / self-signed)

Dependency: requests  (pip install requests)

Contoh:
  python3 pve.py nodes
  python3 pve.py list --node pve
  python3 pve.py status 150
  python3 pve.py start 150
  python3 pve.py clone 9000 150 --name web-01 --full
  python3 pve.py set-cloudinit 150 --ciuser deploy --sshkey ~/.ssh/id_ed25519.pub \
           --ip 192.168.1.150/24 --gw 192.168.1.1
  python3 pve.py resize 150 scsi0 +20G
  python3 pve.py snapshot 150 pre-deploy
  python3 pve.py rollback 150 pre-deploy
  python3 pve.py backup 150 --storage local
  python3 pve.py delete 150
"""
import argparse
import os
import sys
import time
import urllib.parse

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    sys.exit("Butuh 'requests': pip install requests")


class PVE:
    def __init__(self):
        self.host = os.environ["PVE_HOST"]
        self.node = os.environ.get("PVE_NODE", "pve")
        tid = os.environ["PVE_TOKEN_ID"]
        secret = os.environ["PVE_TOKEN_SECRET"]
        self.verify = os.environ.get("PVE_VERIFY_SSL", "false").lower() == "true"
        self.base = f"https://{self.host}:8006/api2/json"
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"PVEAPIToken={tid}={secret}"
        self.s.verify = self.verify

    def _req(self, method, path, **kw):
        r = self.s.request(method, self.base + path, timeout=30, **kw)
        if r.status_code >= 400:
            sys.exit(f"HTTP {r.status_code} {method} {path}: {r.text}")
        return r.json().get("data")

    def get(self, path):
        return self._req("GET", path)

    def post(self, path, data=None):
        return self._req("POST", path, data=data or {})

    def put(self, path, data=None):
        return self._req("PUT", path, data=data or {})

    def delete(self, path):
        return self._req("DELETE", path)

    def wait_task(self, upid, node=None, timeout=1800, interval=2):
        node = node or self.node
        enc = urllib.parse.quote(upid, safe="")
        start = time.time()
        while True:
            st = self.get(f"/nodes/{node}/tasks/{enc}/status")
            if st.get("status") == "stopped":
                if st.get("exitstatus") != "OK":
                    sys.exit(f"Task GAGAL: {st.get('exitstatus')}")
                print(f"  task OK: {upid}")
                return st
            if time.time() - start > timeout:
                sys.exit("Task timeout")
            time.sleep(interval)


def vmtype(pve, node, vmid):
    """Deteksi qemu vs lxc."""
    for t in ("qemu", "lxc"):
        try:
            for v in pve.get(f"/nodes/{node}/{t}"):
                if str(v["vmid"]) == str(vmid):
                    return t
        except SystemExit:
            pass
    sys.exit(f"VMID {vmid} tidak ditemukan di node {node}")


def main():
    p = argparse.ArgumentParser(description="Proxmox VE CLI client")
    p.add_argument("--node", help="override PVE_NODE")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("nodes")
    sub.add_parser("list")
    for c in ("status", "start", "stop", "shutdown", "reboot", "config"):
        sp = sub.add_parser(c); sp.add_argument("vmid")

    sp = sub.add_parser("clone")
    sp.add_argument("template"); sp.add_argument("newid")
    sp.add_argument("--name", required=True); sp.add_argument("--storage", default="local-lvm")
    sp.add_argument("--full", action="store_true")

    sp = sub.add_parser("set-cloudinit")
    sp.add_argument("vmid"); sp.add_argument("--ciuser", required=True)
    sp.add_argument("--sshkey", help="path ke public key")
    sp.add_argument("--ip", help="mis. 192.168.1.150/24 atau dhcp")
    sp.add_argument("--gw"); sp.add_argument("--nameserver", default="1.1.1.1")

    sp = sub.add_parser("resize")
    sp.add_argument("vmid"); sp.add_argument("disk"); sp.add_argument("size")

    sp = sub.add_parser("snapshot")
    sp.add_argument("vmid"); sp.add_argument("name"); sp.add_argument("--desc", default="")

    sp = sub.add_parser("rollback")
    sp.add_argument("vmid"); sp.add_argument("name")

    sp = sub.add_parser("backup")
    sp.add_argument("vmid"); sp.add_argument("--storage", default="local")
    sp.add_argument("--mode", default="snapshot")

    sp = sub.add_parser("delete")
    sp.add_argument("vmid"); sp.add_argument("--purge", action="store_true")

    sp = sub.add_parser("task-wait")
    sp.add_argument("upid")

    args = p.parse_args()
    pve = PVE()
    node = args.node or pve.node

    if args.cmd == "nodes":
        for n in pve.get("/nodes"):
            print(f"{n['node']:<12} {n.get('status','?'):<8} cpu={n.get('cpu',0):.2f} mem={n.get('mem',0)//2**20}MB")

    elif args.cmd == "list":
        for t in ("qemu", "lxc"):
            for v in pve.get(f"/nodes/{node}/{t}"):
                print(f"{v['vmid']:<6} {t:<5} {v.get('name',v.get('hostname','')):<24} {v.get('status','?')}")

    elif args.cmd in ("status", "config"):
        t = vmtype(pve, node, args.vmid)
        path = "status/current" if args.cmd == "status" else "config"
        d = pve.get(f"/nodes/{node}/{t}/{args.vmid}/{path}")
        for k, v in sorted(d.items()):
            print(f"{k}: {v}")

    elif args.cmd in ("start", "stop", "shutdown", "reboot"):
        t = vmtype(pve, node, args.vmid)
        upid = pve.post(f"/nodes/{node}/{t}/{args.vmid}/status/{args.cmd}")
        pve.wait_task(upid, node)

    elif args.cmd == "clone":
        data = {"newid": args.newid, "name": args.name, "storage": args.storage}
        if args.full:
            data["full"] = 1
        upid = pve.post(f"/nodes/{node}/qemu/{args.template}/clone", data)
        pve.wait_task(upid, node)

    elif args.cmd == "set-cloudinit":
        data = {"ciuser": args.ciuser, "nameserver": args.nameserver}
        if args.sshkey:
            key = open(os.path.expanduser(args.sshkey)).read()
            data["sshkeys"] = urllib.parse.quote(key, safe="")
        if args.ip:
            ipc = "ip=" + args.ip
            if args.gw and args.ip != "dhcp":
                ipc += ",gw=" + args.gw
            data["ipconfig0"] = ipc
        pve.put(f"/nodes/{node}/qemu/{args.vmid}/config", data)
        pve.post(f"/nodes/{node}/qemu/{args.vmid}/cloudinit", {})  # regenerate
        print("cloud-init diperbarui")

    elif args.cmd == "resize":
        t = vmtype(pve, node, args.vmid)
        pve.put(f"/nodes/{node}/{t}/{args.vmid}/resize", {"disk": args.disk, "size": args.size})
        print("resize OK")

    elif args.cmd == "snapshot":
        t = vmtype(pve, node, args.vmid)
        upid = pve.post(f"/nodes/{node}/{t}/{args.vmid}/snapshot",
                        {"snapname": args.name, "description": args.desc})
        pve.wait_task(upid, node)

    elif args.cmd == "rollback":
        t = vmtype(pve, node, args.vmid)
        upid = pve.post(f"/nodes/{node}/{t}/{args.vmid}/snapshot/{args.name}/rollback")
        pve.wait_task(upid, node)

    elif args.cmd == "backup":
        upid = pve.post(f"/nodes/{node}/vzdump",
                        {"vmid": args.vmid, "storage": args.storage,
                         "mode": args.mode, "compress": "zstd"})
        pve.wait_task(upid, node, timeout=3600)

    elif args.cmd == "delete":
        t = vmtype(pve, node, args.vmid)
        st = pve.get(f"/nodes/{node}/{t}/{args.vmid}/status/current")
        if st.get("status") == "running":
            print("VM running, stop dulu...")
            pve.wait_task(pve.post(f"/nodes/{node}/{t}/{args.vmid}/status/stop"), node)
        path = f"/nodes/{node}/{t}/{args.vmid}"
        if args.purge:
            path += "?purge=1"
        upid = pve.delete(path)
        if upid:
            pve.wait_task(upid, node)
        print("deleted")

    elif args.cmd == "task-wait":
        pve.wait_task(args.upid, node)


if __name__ == "__main__":
    main()
