---
name: secure-laravel-delivery
description: "Use when delivering Laravel apps to GitHub and VPS hosts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [laravel, security, multi-tenant, docker, vps, github, deployment]
    category: software-development
---

# Secure Laravel Delivery

## Always-on rules

- Treat "implemented" and "deployed" as separate claims; verify each independently.
- Treat "AdminLTE dependency present" and "AdminLTE UX implemented" as different claims: verify the rendered layout has the expected sidebar, responsive toggle, active states, actions, and mobile behavior rather than relying on the stylesheet import.
- Define a UI acceptance pass for every operational module: desktop and mobile layout, list/empty/loading/error states, responsive tables, create/edit/delete workflow, authorization visibility, validation feedback, and post-mutation confirmation.
- Prefer modal CRUD for short master-data forms and dedicated responsive pages for complex workflows such as POS, recipes, PO line items, and financial reconciliation; keep both paths backed by the same validated server endpoints.
- Smoke-test every navigation target as the authenticated role that can see it and capture the actual exception log for any 5xx before changing views or controllers; never declare a broad workflow fixed from static inspection alone.
- Keep secrets, generated credentials, tokens, and production `.env` files outside Git; inspect `.gitignore` before staging.
- Enforce tenant isolation in server-side scopes, policies, and middleware; never trust a branch ID from a request or rely on UI hiding.
- Make privileged role boundaries explicit, including deny paths for central roles barred from tenant financial data.
- Build one vertical slice at a time: schema, authorization, service/controller, view, test, documentation, then refactor. Do not present a broad scaffold as a finished ERP.
- For every completed slice, document the business workflow, role matrix, tenant boundary, deployment impact, and remaining roadmap in Indonesian when the user asks for Indonesian documentation; keep README claims aligned with actual completed modules.
- Treat POS, stock, cash, and PO mutations as server-owned domain operations: calculate prices/totals from database state, use a transaction, lock mutable stock rows, and record an auditable movement.
- Keep tenant financial data private by default: deny central-owner access at route, controller, and service layers; let Owner Mitra see only memberships, and separate employee transaction rights from Owner Mitra reporting rights.
- Treat a cash shift as a reconciliation boundary: require an open shift for POS/manual cash, allow one open shift per branch, and compute expected balance and variance from server-side transactions rather than browser totals.
- Distinguish cash balance from profit: do not label cash-in-minus-cash-out as net profit until HPP and period rules are explicitly modeled.
- Use migrations and seeders for repeatable setup. Read seed credentials from environment variables and never commit demo passwords.
- Use Docker Compose when PHP/MySQL/Composer are unavailable, but distinguish static checks from runtime checks; never claim Laravel tests passed without executing them.
- Pin and commit `composer.lock` for production builds; do not let a Dockerfile silently resolve unconstrained framework versions because Composer security policy can make an otherwise valid constraint fail at build time.
- Preflight virtualization before installing Docker: detect Proxmox LXC/CT, recommend a VM for production, and require explicit opt-in plus nesting/keyctl before attempting Docker-in-LXC.
- Select database images against the actual VM CPU baseline; avoid newer images that require x86-64-v2 when older Proxmox CPUs may lack those instructions.
- Before pushing, run shell syntax checks, `git diff --check`, inspect staged paths, and check for secrets; if PHP/Composer are absent, do not substitute these checks for PHP lint or PHPUnit.
- After a source fix, verify the deployed checkout and the running container independently (`git log`, host file, container file, image/container status); a stale local branch, ignored file, cached Blade view, or restarting container can make a correct commit appear ineffective.
- Support deployment modes explicitly: public domain with ACME, private LAN IP through host Nginx on port 80, and Cloudflare Tunnel without local TLS; keep the container on loopback and allow LAN firewall rules only for the declared subnet.
- Derive `SESSION_SECURE_COOKIE` from the actual external scheme: set it false for HTTP IP/LAN access and true for HTTPS domain or Cloudflare access, because a secure cookie is not sent over HTTP and causes login CSRF/session expiry.
- Make the unauthenticated root path a verified entry point: redirect `/` to `/login` or `/dashboard`, remove the distro default Nginx site, and smoke-test both `/` and `/login` through the same host/IP that users will use.
- After creating or pushing a repository, read back repository metadata and the remote branch/commit; a successful local push command alone is insufficient, and a timed-out readback must be reported as unverified rather than inferred from the push output.

## Procedure

1. Inspect host and repository: PHP, Composer, Node, Docker, database tooling, branch, remotes, worktree, and shallow-clone state.
2. Choose runtime path. Run dependencies, migrations, and tests locally when possible; otherwise create a reproducible Docker path and record runtime verification as pending.
3. Establish the domain model first: users, branches, membership pivot, shared catalog, branch stock, transactions, audit records, timestamps, and statuses. Use foreign keys, indexes, unique constraints, restrictive deletes, and decimal money/quantity types.
4. Add RBAC and tenancy together. Register roles/permissions, seed roles, make membership explicit, and constrain every branch-owned read/write with middleware or policies. Keep authorization in one layer of truth: do not add route permission middleware unless the corresponding permission is seeded and assigned; service-layer checks must still protect direct calls.
5. Add authentication with validation, CSRF, session regeneration on login, invalidation on logout, secure production cookie settings, and `APP_DEBUG=false` defaults.
6. Add deployment artifacts: versioned PHP-FPM, private MySQL network, persistent volumes, healthchecks, non-public database ports, reverse proxy, scheduler/worker, and an idempotent installer with domain/email/root validation. Verify that the app container actually publishes the loopback port consumed by the host reverse proxy, and keep the ACME webroot directory creation before Nginx/Certbot use. For a private LAN install, bind the container to loopback and let host Nginx serve `http://<VM-IP>` on port 80; configure HTTP session cookies and make Nginx redirect `/` to `/login`; for Cloudflare Tunnel, set `APP_URL` to the public URL, use secure cookies, and keep local TLS/ACME disabled.
7. Configure TLS only after DNS points to the host. Use an HTTP ACME webroot, obtain the certificate, then switch to HTTPS and reload only after `nginx -t` succeeds.
8. Verify what is possible: `bash -n deploy/install.sh`, `bash -n deploy/backup.sh`, `git diff --check`, Compose config, PHP lint/tests when available, and a staged-file secret scan. Label skipped checks explicitly. Read backup scripts as well as installers: load `.env` before using database variables, write backups to a permissioned directory, and use `mysqldump --single-transaction` for live InnoDB data. For HTTP LAN mode, verify the container's runtime config reports `session.secure=false`, then test `/` for a redirect and `/login` for `200` through host Nginx before declaring login ready.
9. Prepare GitHub in separate operations: verify auth identity, check target existence, create with explicit visibility, commit, set exact remote, push `main`, then read back visibility, default branch, and commit SHA.
10. If a shallow-clone push fails with missing-object or remote-pack errors, stop retrying the same history. Run `git fsck`, preserve the working tree outside the new Git index, create a fresh history from it, exclude any Git metadata backup directory before staging, and push only after confirming target and force-push scope.
11. For mutating HTTP actions such as receiving PO stock, opening/closing shifts, and recording cash, use POST/PUT/PATCH/DELETE plus CSRF; never expose state-changing domain operations as GET routes. When a relationship is `hasMany`, replace child rows explicitly inside a transaction rather than calling many-to-many `sync()`.
12. Update dependent tests when a new invariant changes an existing flow: for example, if POS requires an open shift, seed an open shift in every POS fixture and add a failure test for missing shifts. Run the focused test before the full suite when the runtime exists.
13. Report changed artifacts, checks that actually ran, verified remote URL/commit, and remaining work. Never call an incomplete module production-ready.

## References

- Read `references/vps-deployment.md` for the Docker/Nginx/Certbot layout, virtualization/CPU gates, Composer lockfile discipline, and private LAN/Cloudflare deployment modes.
- Read `references/operational-ui.md` for the AdminLTE integration, responsive CRUD, modal-vs-page workflow, and route smoke-test acceptance gate.
- Read `references/vertical-slice.md` when implementing a multi-tenant transaction module such as POS, stock, cash, or purchase orders.
- Read `references/financial-privacy.md` when implementing branch cash, shifts, reports, or role-specific financial visibility.
