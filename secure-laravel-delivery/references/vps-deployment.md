# VPS Deployment Reference

Use this reference after the application foundation is committed.

## Preflight

- Confirm Debian/Ubuntu and root access.
- Classify the endpoint before installing: public domain with ACME, private LAN IP via host Nginx on port 80, or Cloudflare Tunnel with local TLS disabled.
- For private LAN mode, collect the VM IP and LAN CIDR; serve `http://<VM-IP>` through host Nginx and keep the container published only on `127.0.0.1:8080`. Set `APP_URL` to the HTTP URL and `SESSION_SECURE_COOKIE=false`; otherwise browsers omit the session cookie on HTTP and login returns a CSRF/session-expiry response.
- For Cloudflare Tunnel mode, set `APP_URL` to the public HTTPS hostname, set `SESSION_SECURE_COOKIE=true`, keep local TLS disabled, and target `http://127.0.0.1:8080` when `cloudflared` is colocated or the VM private IP only when it runs elsewhere.
- Detect Proxmox LXC/CT before installing Docker. Recommend a VM for production; only continue in CT after the operator explicitly enables the documented nesting/keyctl path.
- Check CPU compatibility before selecting images; pin a database image compatible with the oldest supported x86 CPU instead of assuming x86-64-v2.
- Check Docker and Compose availability; install Docker only through the official installation path when absent.
- Reject blank domains, malformed email addresses, and unsafe default passwords.
- Pin and commit `composer.lock`; use `composer install` in production. If bootstrapping an old checkout without a lockfile, resolve once in a controlled build and commit the resulting lockfile rather than leaving builds permanently floating.

## Runtime layout

- Keep MySQL on the private Compose network; publish only the app to loopback, for example `127.0.0.1:8080:80`.
- Put host Nginx in front of the app and proxy to loopback; never expose the database port publicly.
- Persist MySQL data and Laravel storage with named volumes.
- Use healthchecks before starting application migrations.
- Run migrations and seeders explicitly with `--force`; seed only environment-provided owner credentials.

## TLS order

1. Start HTTP Nginx with an ACME webroot location.
2. Create the Nginx symlink, run `nginx -t`, and reload.
3. Run Certbot webroot issuance only after DNS resolves to the VPS.
4. Replace the site with HTTP redirect plus HTTPS certificate paths.
5. Run `nginx -t` again before reload.
6. Open SSH and Nginx Full in UFW only after an SSH path is confirmed.

## Installer gates

- Use `set -Eeuo pipefail`.
- Generate `APP_KEY`, database passwords, and the initial owner password with a cryptographic random source.
- Create `.env` with mode `600`; never print secrets except the one-time owner password, and instruct the operator to rotate it.
- Make directory creation happen before writing ACME webroot files.
- Keep HTTP and TLS heredocs separate; a malformed heredoc can turn a deployment script into invalid Nginx configuration while still passing superficial checks.
- For private LAN mode, remove the distribution's default Nginx site, make the application site the `default_server`, and route `location = /` to `/login`; otherwise an untouched welcome site or stale default can mask the application.
- Run `bash -n` against the installer and `nginx -t` on the target host.

## Verification

After deployment, read back `docker compose ps`, application health, migration status, Nginx configuration, TLS certificate when applicable, and a login request. For HTTP LAN mode, test `curl -I http://127.0.0.1/` for `302` to `/login`, `curl -I http://127.0.0.1/login` for `200`, and inspect `config('session.secure')` inside the app container. Delete old browser cookies after changing secure-cookie settings because a stale secure cookie can obscure a correct server configuration. For CPU or LXC failures, capture the database/container logs before changing volumes; do not destroy a data volume to solve a platform compatibility error.
