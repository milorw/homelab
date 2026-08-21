## Switch to Terraform for LXC Management

### Context

Currently, I am planning to use Ansible for LXC creation/management, but it does not support non-existent LXCs very well, and requires a lot of setup.

### Decision

Switch to Terraform for base LXC management, and use Ansible exlusively for internal LXC management.

### Consequences

Pros

- Separate config for LXC creation and for interal LXC services
- Less custom Ansible tooling for LXC management

Cons

- Requires a github repo structure change
- More services, more files, and more initial setup
