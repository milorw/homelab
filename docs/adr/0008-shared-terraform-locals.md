## Shared Terraform Locals for LXC Config

### Context

Currently, each LXC resource file (`lxc-*.tf`) has its own hardcoded IP, gateway, bridge, and (for samba) storage mount paths. This means there's no single place to see every LXC's IP allocation at a glance, and has the risk of duplicating a host storage path across LXCs with a typo.

### Decision

Added `terraform/locals.tf` with `lxc_ips`, `network` (gateway/bridge), and `storage` maps so per-LXC resources reference these instead of literals. This also keeps each LXC as its own resource file rather than the unused generic `for_each` pattern that was in `main.tf`.

### Consequences

Pros

- Fewer duplicated hardcoded values
- Cleaner file/folder structure
- Less chance for typos to appear

Cons

- N/A
