# Proxmox Homelab

This repository serves as storage and reference documentation for my personal homelab. The code provided here is not designed for usage elsewhere, and likely will not work outside of this environment.

Ansible and Terraform are the source of truth for this setup: every LXC is managed by Terraform, and every service/LXC is initially set up and then maintained by Ansible.

## Architecture
Proxmox has a primary storage location (`tank/`) that contains all service appdata, NAS user files, and Jellyfin storage. My phyiscal hard drives are mirrored for redundancy on all app data and user files, while Jellyfin media sits on a single drive (which doesn't store any critical data). Where possible, app data and configuration are managed by Ansible, which requires no safety/redundancy, as a play can be re-run at any time for lost data/config.

- `tank/appdata/...` - stores all non-Ansible service data (such as app databases)
- `tank/shares...` - owned by Samba, all NAS user files
- `tank/jellyfin/...` - owned by Jellyfin, all media files
- `tank/backups/...` - managed by Proxmox, all system backups

Proxmox also hosts a "router" LXC (Caddy + CoreDNS + HAProxy), which provides custom domain resolution and HTTPS over Tailscale or on my LAN network. Domain resolution is purposefully not made available to wider internet for security, but launching Tailscale and then navigating to a simple URL allows non-technical users to connect to services quickly. The router is also a Tailscale subnet router for the LXCs, so SMB and SSH work remotely.

### LXCs

| ID | LXC | Runs | Playbook |
|---|---|---|---|
| 100 | `samba` | Samba NAS shares | `lxc-samba.yml` |
| 104 | `docker_apps` | Homebox, Ombi, Sure, Mealie, Homepage (Docker Compose) | `docker-apps.yml` |
| 105 | `edge_router` | Caddy, CoreDNS, HAProxy (Docker Compose), Tailscale | `edge-router.yml` |
| 106 | `jellyfin` | Jellyfin, with Intel VAAPI transcoding | `lxc-jellyfin.yml` |
| 110 | `minecraft` | Crafty Controller running a Paper server (Docker Compose) | `lxc-minecraft.yml` |

`lxc-baseline.yml` applies settings shared by every LXC.

## Repository layout

- `ansible/` - Ansible playbooks
  - `../inventory/` - static inventory for the Proxmox node, the Proxmox plugin for LXCs/VM inventory, and group vars (including Vault-encrypted secrets)
  - `../playbooks/` - Ansible entry points
    - `../files/`, `../tasks/`, `../templates/` - supporting files and config for Ansible plays
- `terraform/` - Terraform-managed infrastructure
- `docs/` - reference notes

## CI & local workflow

Every push/PR to `main` and every local commit run the same checks: `Gitleaks` for secret scanning, `yamllint` and `ansible-lint` for Ansible files, and `terraform fmt`, `terraform validate` and `tflint` for Terraform files. See `docs/` for more details.
