# Proxmox Homelab

This repository serves as storage and reference documentation for my personal homelab. The code provided here is not designed for usage elsewhere, and likely will not work outside of this environment.

Ansible and Terraform are the source of truth for this setup: every LXC is managed by Terraform, and every service/LXC is initially set up and then maintained by Ansible.

## Architecture
Proxmox has a primary storage location (`tank/`) that contains all service appdata, NAS user files, and Jellyfin storage. My phyiscal hard drives are mirrored for redundancy on all app data and user files, while Jellyfin media sits on a single drive (which doesn't store any critical data). Where possible, app data and configuration are managed by Ansible, which requires no safety/redundancy, as a play can be re-run at any time for lost data/config.

- `tank/appdata/...` - stores all non-Ansible service data (such as app databases)
- `tank/shares...` - owned by Samba, all NAS user files
- `tank/jellyfin/...` - owned by Jellyfin, all media files
- `tank/backups/...` - managed by Proxmox, all system backups

Proxmox also hosts a "router" LXC (Caddy + CoreDNS), which provides custom domain resolution over Tailscale or on my LAN network. Domain resolution is purposefully not made available to wider internet for security, but launching Tailscale and then navigating to a simple URL allows non-technical users to connect to services quickly.

## Repository layout

- `ansible/` - Ansible playbooks
  - `../inventory/` - static inventory for the Proxmox node, the Proxmox plugin for LXCs/VM inventory, and group vars (including Vault-encrypted secrets)
  - `../playbooks/` - Ansible entry points
    - `../files/`, `../tasks/`, `../templates/` - supporting files and config for Ansible plays
- `terraform/` - Terraform-managed infrastructure
- `docs/` - reference notes

## CI & local workflow

Every push/PR to `main` and every local commit run the same checks: `Gitleaks` for secret scanning, `yamllint`, and `ansible-lint` for file consistency. See `docs/` for more details.
