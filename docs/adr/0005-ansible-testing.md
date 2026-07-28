## Do Not Use Molecule For Ansible Testing

### Context

Molecule integrates with Ansible for testing, but it does not include built-in support for the Proxmox plugin.

### Decision

Do not write custom hooks for Molecule, instead create separate validation playbooks for the live Proxmox LXCs.

### Consequences

Pros

- Less backend maintenance
- Simpler setup
- No need for matrix testing with Proxmox

Cons

- Manual testing is more prone to mistakes
- Testing on live servers is not ideal
