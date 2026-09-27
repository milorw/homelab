## Drop Ansible Roles for Playbooks and Shared Task Files

Supersedes ADR 0004.

### Context

ADR 0004 split reusable components into roles. In practice the only role ever written was `lxc_base`, which created and provisioned LXCs. Once Terraform took over LXC creation (ADR 0007), that role had nothing left to do, and the remaining shared code (installing Docker) was a single small task list.

### Decision

Remove `ansible/roles/` (the `lxc_base` role was deleted with the Terraform switch). Each LXC gets one playbook (`ansible/playbooks/<name>.yml`), and anything shared between playbooks lives in a task file under `ansible/playbooks/tasks/`, pulled in with `include_tasks` (e.g. `tasks/docker.yml`).

### Consequences

Pros

- Each LXC's setup reads top to bottom in one file
- Less structure and fewer variable indirections to maintain

Cons

- Less formal reuse - if a lot more shared logic appears, roles may be worth revisiting
