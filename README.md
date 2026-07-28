# Proxmox Homelab

This repository serves as storage and reference documentation for my personal homelab. The code provided here is not designed for usage elsewhere, and likely will not work outside of this environment.

Ansible is the source of truth for this setup: every LXC and service is defined as a role/playbook, applied to my Proxmox node over its API or SSH.

## Architecture

## Repository layout

- `inventory/` - static inventory for the Proxmox node, the Proxmox plugin for LXCs/VMs, and group vars (including Vault-encrypted secrets)
- `roles/` - Reusable Ansible components
- `playbooks/` - Ansible entry points
- `docs/` - reference notes

## Validation

Molecule isn't a good fit because it has no dedicated Proxmox driver, and there's no spare node to test against. Instead, each service gets its own verification playbook, separate from the playbook that creates it, which checks the live LXC actually matches the intended state.

## CI & local workflow

Every push/PR to `main` and every local commit run the same checks: `Gitleaks` for secret scanning, `yamllint`, and `ansible-lint`. See `docs/` for more details.
