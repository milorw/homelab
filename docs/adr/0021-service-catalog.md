## Service Catalog as the Single Place to Register a Service

Amends ADR 0014 (the homepage is now generated from the catalog rather than from the edge router's lists), and replaces the hand-written service lists described in ADR 0011.

### Context

Adding a service meant editing several files that all had to agree: its port in `group_vars/all/service_ports.yml`, an `edge_services` entry and a line in each `edge_domains` list in `edge_router.yml` (plus an IP lookup var for a new LXC), and a `homepage_service_meta` and `homepage_docker_containers` entry in `docker_apps.yml`. The per-service lists in `edge_router.yml` also sat in the middle of settings that are set once and rarely touched (Cloudflare tokens, error-page timings, Tailscale routes).

### Decision

Add `ansible/inventory/group_vars/all/services.yml`, with one entry per service holding everything about it: `port`, `host` (inventory group) or `address`, `domains`, and optional `subdomain`, `proxy` (Caddy), `tcp` (HAProxy), `homepage`, `container` and `firewall`. The vars the templates use are now generated from it with short Jinja blocks:

- `service_ports` - at the bottom of `services.yml` (`service_ports.yml` is removed)
- `edge_domains`, `edge_services`, `edge_tcp_services` - in `edge_router.yml`, which keeps only each domain's Cloudflare env var name (`edge_domain_settings`) and its own settings
- `homepage_service_meta`, `homepage_docker_containers` - in `docker_apps.yml`

The templates themselves are unchanged. The homepage still lists only services that every domain serves, but that list now comes from the catalog's `domains` instead of the edge router's hand-written lists. The catalog's order is the order services appear on the homepage.

### Consequences

Pros

- Adding a service is one catalog entry, plus the app's own playbook and templates
- Settings that are set once no longer sit between per-service lists
- No IP lookup var per LXC; addresses come from `host`

Cons

- Some logic now lives in vars files, as Jinja blocks - the least readable part, and they need `{%-`/`-%}` whitespace trimming or the result silently becomes a string instead of a dict
- `service_ports` gains entries for things that are only proxied (`proxmox`, `ha`)
