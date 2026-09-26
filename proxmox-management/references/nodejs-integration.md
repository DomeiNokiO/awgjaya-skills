# Integrasi Node.js (Axios)

Client Proxmox untuk Node.js. Dua mode auth: **API token** (disarankan untuk backend/otomasi) dan **ticket** (login user interaktif).

## Setup

```bash
npm install axios qs
```

`.env`:

```
PVE_HOST=192.168.1.10
PVE_NODE=pve
PVE_TOKEN_ID=automation@pve!automate
PVE_TOKEN_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## Client berbasis API Token (disarankan)

```javascript
import axios from 'axios';
import qs from 'qs';
import https from 'node:https';

const BASE = `https://${process.env.PVE_HOST}:8006/api2/json`;

const pve = axios.create({
  baseURL: BASE,
  headers: {
    Authorization: `PVEAPIToken=${process.env.PVE_TOKEN_ID}=${process.env.PVE_TOKEN_SECRET}`,
  },
  // Self-signed cert: bypass HANYA di lingkungan terpercaya.
  httpsAgent: new https.Agent({ rejectUnauthorized: false }),
});

// POST/PUT wajib form-urlencoded, bukan JSON.
function form(data) {
  return qs.stringify(data);
}

export { pve, form };
```

## Client berbasis Ticket (login password)

```javascript
import axios from 'axios';
import https from 'node:https';

async function loginTicket(host, username, password) {
  const agent = new https.Agent({ rejectUnauthorized: false });
  const { data } = await axios.post(
    `https://${host}:8006/api2/json/access/ticket`,
    new URLSearchParams({ username, password }).toString(),
    { httpsAgent: agent, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
  );
  const { ticket, CSRFPreventionToken } = data.data;
  // ticket → cookie PVEAuthCookie; CSRF → header untuk POST/PUT/DELETE
  return axios.create({
    baseURL: `https://${host}:8006/api2/json`,
    httpsAgent: agent,
    headers: {
      Cookie: `PVEAuthCookie=${ticket}`,
      CSRFPreventionToken,
    },
  });
}
```

## Pola async: tunggu task (UPID) selesai

```javascript
async function waitTask(node, upid, { interval = 1500, timeout = 300000 } = {}) {
  const start = Date.now();
  for (;;) {
    const { data } = await pve.get(`/nodes/${node}/tasks/${encodeURIComponent(upid)}/status`);
    const s = data.data;
    if (s.status === 'stopped') {
      if (s.exitstatus !== 'OK') throw new Error(`Task gagal: ${s.exitstatus}`);
      return s;
    }
    if (Date.now() - start > timeout) throw new Error('Task timeout');
    await new Promise((r) => setTimeout(r, interval));
  }
}
```

## Operasi umum

```javascript
const node = process.env.PVE_NODE;

// List VM
const { data: vms } = await pve.get(`/nodes/${node}/qemu`);

// Start VM → tunggu selesai
async function startVM(vmid) {
  const { data } = await pve.post(`/nodes/${node}/qemu/${vmid}/status/start`);
  return waitTask(node, data.data); // data.data = UPID
}

// Clone dari template
async function cloneVM(templateId, newid, name) {
  const { data } = await pve.post(
    `/nodes/${node}/qemu/${templateId}/clone`,
    form({ newid, name, full: 1, storage: 'local-lvm' }),
  );
  return waitTask(node, data.data);
}

// Set cloud-init
async function setCloudInit(vmid, { ciuser, sshkeys, ip, gw }) {
  await pve.put(
    `/nodes/${node}/qemu/${vmid}/config`,
    form({
      ciuser,
      sshkeys: encodeURIComponent(sshkeys), // WAJIB url-encode
      ipconfig0: `ip=${ip},gw=${gw}`,
      nameserver: '1.1.1.1',
    }),
  );
}

// Backup
async function backupVM(vmid) {
  const { data } = await pve.post(
    `/nodes/${node}/vzdump`,
    form({ vmid, storage: 'local', mode: 'snapshot', compress: 'zstd' }),
  );
  return waitTask(node, data.data, { timeout: 1800000 });
}

// Delete aman: pastikan stopped dulu
async function deleteVM(vmid) {
  const { data: st } = await pve.get(`/nodes/${node}/qemu/${vmid}/status/current`);
  if (st.data.status === 'running') {
    const { data } = await pve.post(`/nodes/${node}/qemu/${vmid}/status/stop`);
    await waitTask(node, data.data);
  }
  const { data } = await pve.delete(`/nodes/${node}/qemu/${vmid}?purge=1`);
  return waitTask(node, data.data);
}
```

## Pitfalls Node.js

- **`json:` vs form:** kirim string `qs.stringify(...)`, jangan object JSON — banyak endpoint tolak JSON mentah.
- **UPID encoding:** UPID mengandung `:`; `encodeURIComponent` saat menaruhnya di path task.
- **sshkeys:** `encodeURIComponent` seluruh blok; newline → `%0A`.
- **rejectUnauthorized:false** hanya untuk jaringan terpercaya; produksi pasang CA benar.
- **Selalu `waitTask`** setelah aksi mutasi — respons awal cuma UPID, bukan tanda sukses.
