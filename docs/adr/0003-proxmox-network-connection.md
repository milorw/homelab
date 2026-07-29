## Define Proxmox -> Ansible Connection

### Context

Ansible needs to communicate with Proxmox in order to create and manage LXCs.

### Decision

Define an Ansible role in Proxmox with a token/secret pair, then allow the Ansible Proxmox plugin to use that authentication.

### Consequences

Pros

- More secure than username/password auth

Cons

- Requires strong Ansible user permissions on the Proxmox host
