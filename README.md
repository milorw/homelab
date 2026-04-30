# Homelab

This repository is primarily written for future me, not as a guide to follow. It serves as the source of truth for the parts of my homelab that I have customized enough to want under version control. It covers the LXC layout, Docker compose files, edge routing setup, and notes about how storage and shared config paths fit together.

## What This Repo Covers

- Proxmox LXC layout and the roles of each container
- Docker compose files for all of my self-hosted services
- DNS / reverse-proxy routing through a dedicated router LXC
- Custom Caddy and CoreDNS config script
- Notes about storage, mountpoints, and shared paths

## Current Architecture

At a high level, the homelab is split up by responsibility, instead of running everything in the same place.

- A dedicated router LXC handles inbound access for private services.
- A Docker LXC hosts all Dockerized application containers.
- A Samba LXC handles any file shares.
- Jellyfin runs in its own LXC (created from a community script, and not stored in this repo).

For remote access, the router flow is:

1. Client requests a service subdomain.
2. Tailscale's split DNS resolves that name through the router LXC.
3. CoreDNS maps approved service names to the router's Tailscale IP.
4. Caddy receives the request on the router and reverse proxies to the target service.

LAN access is similar, except that my LAN router forwards its DNS traffic to the router LAN IP, and Caddy reverse proxies from the router's LAN ip.

This setup allows me to have one controlled entry point while still exposing all of my internal services.

## Config Organization

One of the main goals of this setup is to keep path conventions the same across the server.

- Repo-managed config is grouped under `service_configs/`.
- Each LXC gets its relevant config folder mounted into `/opt/...`.
- Persistent application data lives under `/srv/appdata/...` inside the containers.
- Storage on the host is grouped into datasets and folders under `tank/`.

## Services Currently Represented Here

- `homebox`: home inventory app
- `ombi`: media request app
- `shairport-sync` + `snapserver`: audio streaming stack
- `sure`: personal finance app
- `caddy`: reverse proxy on the router LXC
- `coredns`: DNS responder on the router LXC
- `generator`: custom Python tool to write Caddy/CoreDNS config from YAML input

## Storage Snapshot

The main storage root is a `tank` hierarchy with appdata, backups, media, and shares separated for easier management.

```text
tank
├── appdata
│   ├── edge_data
│   ├── homebox_data
│   ├── ombi_data
│   ├── shairport_data
│   ├── snapserver_data
│   └── sure_data
├── backups
├── jellyfin
└── shares
    ├── share1
    ...
```

- service data is persistent even if containers are rebuilt
- backups have their own dataset (to enforce a size limit)
- shares are separated into their own datasets (with unique encryption keys)
- app configs and app data stay separate

## Documentation Map

Deeper notes on the setup that I've created live in [docs/README.md](docs/README.md).
