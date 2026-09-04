## HAProxy for Raw-TCP Services Behind the Edge Router

### Context

- Caddy's `reverse_proxy` is currently HTTP-only, but Minecraft's protocol isn't HTTP, so it can't go through the same Caddy service blocks as homebox/sure/proxmox/jellyfin/ombi/ha.

Some options considered:
- Caddy's `layer4` plugin (another xcaddy build, heavier dependency tree)
- plain TCP forward via a second lightweight proxy, or skip routing through the edge router entirely (direct LAN/tailnet IP:port).

Preferably, would have a port-less connection experience (i.e `minecraft.domainname`, no `:25565`).

### Decision

Decided to go with `haproxy:lts` (official prebuilt image, no compiling) as a third Docker Compose service, for TCP passthrough only, and config templated from `edge_tcp_services`.

### Consequences

Pros

- Port-less connection works
- Less build overhead and maintenance

Cons

- Extra docker service added
- Somewhat more complex network routing
