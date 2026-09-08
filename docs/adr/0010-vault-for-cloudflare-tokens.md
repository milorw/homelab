## Ansible Vault for Cloudflare API Tokens

### Context

The old edge router setup kept Cloudflare API tokens in a plaintext `.env` file. This new repo already has a precedent (`vault_pve_token_secret`) for handling API tokens via `ansible/inventory/group_vars/all/vault.yml`.

### Decision

Added `vault_cf_api_token_milorw` / `vault_cf_api_token_owennwb` to `vault.yml`, and `edge_router.yml` references them via `cf_api_token_*` indirection vars, same pattern as the Proxmox token.

### Consequences

Pros

- No more cleartext API secrets sitting in the repo.

Cons

- N/A
