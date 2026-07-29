## Update Ansible Vault to Work Locally and Remotely (in CI tasks)

### Context

Currently, `ansible-lint` in CI tasks does not work because it doesn't have access to the 1Password vault script in order to fetch the Ansible vault password.

### Decision

Swap Ansible config to use the `ANSIBLE_VAULT_PASSWORD_FILE` env variable, so that it can fallback to not using a vault password.

### Consequences

Pros

- Allows CI tasks to run without failure

Cons
