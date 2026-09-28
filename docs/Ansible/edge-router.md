## Edge Router (Caddy + CoreDNS + HAProxy)

The edge router (LXC 105) gives every service a hostname like `mealie.milorw.me`, with HTTPS, reachable on the LAN and over Tailscale. It is configured by `ansible/playbooks/edge-router.yml`, which targets the `edge_router` inventory group (from the `role_edge_router` Proxmox tag).

```bash
cd ansible
ansible-playbook playbooks/edge-router.yml
```

Three services run under Docker Compose in `/opt/edge` (see [ADR 0011](../adr/0011-edge-router-docker-compose.md)):

| Service | Does |
|---|---|
| CoreDNS | Answers `<service>.<domain>` with the edge router's own addresses; forwards everything else to 1.1.1.1 / 8.8.8.8 |
| Caddy | Reverse proxy for HTTP services, with Let's Encrypt certificates via Cloudflare DNS-01 |
| HAProxy | Plain TCP forwarding for services that aren't HTTP, like Minecraft - see [ADR 0009](../adr/0009-haproxy-for-tcp-services.md) |

### Configuration

Services are registered in the service catalog, `ansible/inventory/group_vars/all/services.yml` - see [ADR 0021](../adr/0021-service-catalog.md). Each entry's `domains`, `proxy`, `tcp` and `subdomain` fields decide how the edge router serves it. `ansible/inventory/group_vars/edge_router.yml` holds the rest:

- `edge_domain_settings` - each domain, and the env var its Cloudflare token is passed in. Adding a domain starts here.
- The error-page and Tailscale settings described below.
- Generated from the catalog, and read by the templates:
  - `edge_domains` - each domain with the hostnames it serves, in catalog order
  - `edge_services` - one Caddy entry per catalog service with a `proxy` block: backend `address`/`port`, response `encodings`, and optionally `transport_http` and `headers`
  - `edge_tcp_services` - one HAProxy forward per catalog service with `tcp: true`, on the same port at both ends
  - `edge_backend_addresses` - each service's backend address: its literal `address` if it has one (Home Assistant, which this repo doesn't manage), otherwise the first host in its `host` inventory group. No IP managed by this repo is written down twice.

A service is served as `<name>.<domain>`, or `<subdomain>.<domain>` if it sets one - crafty's panel is `mcpanel`.

The Cloudflare tokens come from the vault - see [ADR 0010](../adr/0010-vault-for-cloudflare-tokens.md) - and are rendered into `/opt/edge/.env` (`0600`).

### Addresses

CoreDNS answers each hostname with **both** the edge router's Tailscale IP and its LAN IP, and Caddy and HAProxy listen on both. The same hostname works whether or not the client is on the tailnet.

The Tailscale IP isn't a static var. The play reads `tailscale status --json` and sets `edge_tailscale_ip` from it. If Tailscale isn't connected (`BackendState != Running`), the play fails with the reason, including the login URL if one is needed, instead of carrying on with a missing IP.

### HTTPS backends with self-signed certificates

Proxmox's web UI is HTTPS-only with a self-signed certificate. Its catalog entry sets `proxy.transport_http: [tls_insecure_skip_verify]`, which renders as:

```
reverse_proxy 192.168.68.90:8006 {
  transport http {
    dial_timeout 5s
    tls_insecure_skip_verify
  }
}
```

No `https://` prefix on the address, and no bare `tls` line - this took a long debugging session to land on. `transport_http` is a list, because every service's `transport http` block also carries the dial timeout (below).

### Error pages

No service should ever hand a client a raw 502 - see [ADR 0015](../adr/0015-edge-router-error-pages.md). Every HTTP service gets:

- `handle_errors 502 503 504` → `unreachable.html`, when Caddy got no response at all
- `handle_response` on a 502/503/504 from the backend itself → `starting.html`
- `dial_timeout` (`edge_dial_timeout`, 5s). A powered-off host drops connections rather than refusing them, so without this the browser waits minutes before showing anything.

Both pages are rendered from `templates/edge_router/error.html.j2` onto the edge router's own disk, fully inline, so they can be served exactly when the app host can't.

**`unreachable.html` is the page you'll actually see**, including during a slow boot. A published container port goes straight to the container, so an app that hasn't bound its port yet refuses the connection exactly like a stopped stack - nothing at the edge router tells "stopped" from "starting". (Confirmed by probing a running container with nothing listening: LAN IP → `connection refused`, host loopback → `connection reset`, because only loopback goes through docker-proxy. Don't try to rebuild the distinction from `{err.message}`.) `starting.html` only fires for an app that answers a gateway 5xx itself, which none currently do.

The page retries the original URL `edge_error_max_attempts` times, `edge_error_retry_delay` seconds apart, then hands off to the homepage (`edge_homepage_service`) after `edge_error_handoff_delay` seconds. On the homepage's own hostname it just stops retrying. A manual refresh restarts the count (told apart from a scripted retry by the browser's navigation type), and the handoff clears the stored count so coming back later doesn't bounce straight to the homepage.

Both responses carry `Cache-Control: no-store`, since an error page cached at the app's own URL would outlive the outage. There is deliberately **no** `fail_duration`. Each site logs failed requests only (`log { level ERROR }`), and the `edge-router · <mode>` footer names which page you're on.

### Applying changes

- Corefile or `haproxy.cfg` changed → that container is restarted.
- `.env` changed → the whole stack is recreated, since env vars are only read when a container is created.
- The Caddyfile is reloaded (`caddy reload`) on every run. It's a no-op when nothing changed, and it means a Caddyfile rendered by a failed run can't stay unloaded.
- Error pages are read from disk on every request, so a change is live as soon as it's rendered.

---

## Tailscale subnet router

The edge advertises one `/32` route per LXC to the tailnet, so remote devices can reach those LXCs at their LAN addresses. This is what covers the things the reverse proxy can't carry: **SMB on samba**, and **SSH to the LXCs**, none of which are tailnet members themselves. Everything HTTP already goes through Caddy, and minecraft through HAProxy. See [ADR 0016](../adr/0016-tailscale-subnet-router.md).

Both settings are managed by the playbook (`edge_tailscale_advertise_routes`, `edge_tailscale_snat_subnet_routes`). They used to be hand-set state on the container, invisible to this repo. The route list is built from the `proxmox_all_lxc` inventory group, so a new LXC gets a route without its IP being written down again. The play fails if that list comes out empty, then only runs `tailscale set` when the current settings differ, and checks afterwards that they took.

**A newly advertised route starts out unapproved.** It carries no traffic until it's approved in the Tailscale admin console.

### SNAT is deliberately off

`--snat-subnet-routes=false`. With SNAT on, the subnet router rewrites remote traffic to its own LAN address, so **every guest sees tailnet users as `edge_router`**, and firewall rules can't tell a remote user from the reverse proxy.

### The return route is not optional

Without SNAT the guests reply to `100.x` addresses, and their default gateway has no idea where that range lives. **A static route on the LAN router is required:**

| Field | Value |
|---|---|
| Destination | `100.64.0.0` |
| Mask | `255.192.0.0` (`/10`) |
| Gateway | `192.168.68.96` |

On the router rather than per-guest, so it also covers devices Ansible doesn't manage. Without it, remote access fails silently - the edge looks healthy, packets arrive, replies vanish.

### Why the Proxmox host isn't routed

The routes used to cover the whole LAN, and with Tailscale up the host was unreachable at `192.168.68.90`. The host is *itself* a tailnet member, so the path was asymmetric: the request arrived via the edge, but the host answered over its own `tailscale0` while the packet still carried its LAN source address, and it was dropped. SNAT used to hide this by making the request look like it came from the edge.

It affects only devices that are both on the LAN and on the tailnet - the host and the edge. The LXCs aren't tailnet members, so they reply through the default gateway into the static route above, which is why they work.

Per-LXC `/32`s fixed it, because `.90` is no longer inside any advertised route and stays on the LAN where the path is symmetric. **Don't widen the routes back to the whole subnet** - the problem comes back the moment `.90` is inside an advertised route again.

The host's own tailnet membership is a deliberate break-glass path for when the edge router is down. With no edge there's no subnet route, so the host's `100.x` address is simply the only way in. Pointing the inventory at that address permanently would turn the backdoor into the front door, which is why it stays on the LAN IP.
