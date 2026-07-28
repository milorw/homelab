## Use 1Password CLI

### Context

Ansible Vault requires a password to be entered in order to decrypt the vault, and this password needs to be stored somewhere.

### Decision

Write a shell script to hook the 1Password CLI into Ansible, allowing it to pull the vault password from the 1Password vault.

### Consequences

Pros

- Less secrets to store securely
- Clearly defined/idempotent storage location

Cons

- Requires 1Password validation on most Ansible commands
