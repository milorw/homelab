## Edge Router: Docker Compose + Ansible/Jinja2 Config Generation

### Context

The old edge router setup generated its Caddyfile and Corefile with a standalone Python container that read `ip.yaml`, run as part of the Docker Compose stack. With Ansible now managing the LXC, config generation could move into Ansible/Jinja2 instead, which is safer and keeps everything in one tool. The remaining choice was whether to keep Caddy + CoreDNS as Docker containers or run them natively as systemd units.

### Decision

Keep Caddy + CoreDNS (and later HAProxy, see ADR 0009) as Docker Compose services, with Ansible owning everything around them:

- `edge-router.yml` installs Docker, renders `Corefile`, `Caddyfile`, `haproxy.cfg` and `.env` from templates in `ansible/playbooks/templates/edge_router/`, deploys the compose project to `/opt/edge`, and brings it up.
- `ansible/inventory/group_vars/edge_router.yml` is the single source of truth for domains and services (ported from `ip.yaml`), including each domain's Cloudflare env var name and each service's reverse proxy backends.
- Caddy is built locally with the `caddy-dns/cloudflare` plugin (`files/edge/caddy/Dockerfile`) for DNS-01 certificates.
- Config changes are applied with `docker compose restart` handlers for CoreDNS and HAProxy, a stack recreate for `.env` changes, and a `caddy reload` that runs on every play.
- The LXC has no persistent mounts: everything except certificates is re-rendered from this repo.

### Consequences

Pros

- Config generation lives in the same tool and repo as everything else
- No custom Python generator to maintain
- Services stay easy to upgrade as container images

Cons

- Docker is a dependency of the edge router LXC
- Building Caddy with xcaddy needs extra disk space
