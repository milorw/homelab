This repo is the primary storage for all of my Proxmox LXC configs, as well as any other scripts or custom setup that I've created.

## Overview

### Remote Access

The primary access point for my server is a router LXC (`service_configs/edge_services`).

1. Tailnet split DNS redirects domain traffic → router CoreDNS
2. CoreDNS validates router's Tailscale IP
3. Client connects to router LXC and hits Caddy to get a reverse proxy

To simplify router management, I created a custom YAML service list and Python parser to generate the Caddyfile and Corefile automatically.

### LXCs

Besides the router, I have separate LXCs for:

- Docker containers (`service_configs/docker_services`)
- Samba shares (`service_configs/samba`)
- Jellyfin (no specific config stored)

Because all of my config lives in the same location, I was able to mount each `service_configs` subfolder at `/opt/…` in each LXC, so I don't need to remember where the configs are. I also have an `appdata` folder mounted at `/srv/appdata/…_data`, allowing my Dockerfiles to mount at the same location.

### Storage

My primary storage is a "tank" folder which contains all of the storage for my server:

```text
tank
├── appdata
│   ├── edge_data
│   ├── homebox_data
│   ├── ombi_data
│   ├── shairport_data
│   ├── snapserver_data
│   └── sure_data
├── backups
│   └── …
├── jellyfin
│   └── …
└── shares
   └── …
```

Inside of this folder, I have several ZFS datasets:

- `media/jellyfin`: Single-drive, large capacity for Jellyfin
- `tank`: mirrored ZFS pool for redundancy
- `tank/backups`: size-limited dataset to prevent backups from exploding
- `tank/shares/…`: per-user NAS share dataset to allow for unique encryption keys
