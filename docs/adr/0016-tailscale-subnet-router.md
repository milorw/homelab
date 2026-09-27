## Manage the Edge Router's Tailscale Subnet Routes (Per-LXC, No SNAT)

### Context

The edge router was hand-configured as a Tailscale subnet router for the whole LAN, with SNAT on. That state wasn't recorded anywhere in this repo. SNAT made every remote packet look like it came from the edge router, so firewall rules couldn't tell a tailnet user from the reverse proxy. Routing the whole LAN also covered the Proxmox host, which is a tailnet member itself, making its return path asymmetric and breaking access to it at its LAN IP while Tailscale was up.

### Decision

`edge-router.yml` now manages the subnet router settings:

- Advertise one `/32` per LXC, built from the `proxmox_all_lxc` inventory group, rather than the whole LAN. The Proxmox host is deliberately left out.
- Turn SNAT off (`edge_tailscale_snat_subnet_routes: false`), so the original `100.x` source address reaches the guest.
- Only run `tailscale set` when the current settings differ, and assert afterwards that they took.

### Consequences

Pros

- The routing setup is in the repo instead of hand-set on the container
- Remote traffic keeps its real source address, so per-source firewall rules work
- A new LXC gets a route without its IP being written down twice

Cons

- Requires a static return route for `100.64.0.0/10` via the edge router on the LAN router
- Newly advertised routes start unapproved and must be approved in the Tailscale admin console
