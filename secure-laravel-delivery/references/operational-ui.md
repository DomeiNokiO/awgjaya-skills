# Operational UI Reference

Use this reference when a Laravel application needs an admin dashboard that is usable on desktop and mobile.

## Layout acceptance

- Use AdminLTE's structural classes and behavior, not only its CDN CSS/JS. Verify the rendered DOM has a real app wrapper, header, sidebar, content region, responsive toggle, and active navigation state.
- Keep the desktop sidebar and mobile drawer separate from page content; do not replace them with a horizontal link row that clips on narrow screens.
- Use a restrained visual system: one accent color, readable contrast, compact page headers, consistent card radius, table headers, badges, and action buttons. Avoid decorative gradients and dashboard clutter.
- Test at a narrow mobile viewport: no horizontal page overflow, no clipped logout/menu controls, and sidebar closure after navigation.

## CRUD acceptance

- Put search/filter, total count, primary action, empty state, validation errors, success feedback, pagination, status badges, and row actions in every list screen.
- Use a modal for short create/edit forms such as ingredients; use a dedicated responsive page for recipes, POS line items, PO lines, and financial workflows where the form needs more space.
- Keep delete/deactivate actions explicit and authorized. Preserve server-side validation and CSRF for modal forms; a modal is only a presentation change, not a security boundary.
- Make list rendering null-safe for optional relationships and show an intentional empty state rather than allowing a missing relation to produce a 500.

## Runtime smoke test

For each authenticated role, run the actual app after rebuilding the image and clearing framework/view caches:

```bash
git log -1 --oneline
sudo docker compose ps
sudo docker compose exec -T app php artisan optimize:clear
sudo docker compose exec -T app php artisan route:list
curl -I http://127.0.0.1/login
```

Then request each visible navigation target. On any 500, immediately collect the matching `production.ERROR`, SQLSTATE, or exception from `storage/logs/laravel.log` and container logs before editing code. Test both the host checkout and the file inside the running container when a source fix appears ineffective.

## Completion gate

Do not call the UI complete until the dashboard, each visible list, at least one create/edit flow per CRUD family, logout, role restrictions, mobile navigation, and empty/error states have been exercised. Record skipped runtime checks explicitly; static Blade inspection is not a substitute for rendering the page.
