## Use Ansible Roles

### Context

Playbooks are becoming tricky to write all into a single playbook, and requires duplicated code between services.

### Decision

Split reusable components into reusable Ansible roles.

### Consequences

Pros

- Easier testing
- Reusable code (not duplicated code)
- Cleaner project setup

Cons

- More variables to pass around
