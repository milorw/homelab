## Validate Inside Each Playbook Instead of Separate Test Playbooks

Supersedes ADR 0005.

### Context

ADR 0005 chose separate validation playbooks over Molecule. The only one written was `test.yml`, which was reworked for the Terraform switch and then removed when the samba playbook replaced it. Separate playbooks also have to be remembered and run on their own, so they drift from the playbooks they check.

### Decision

Still no Molecule. Each playbook checks its own assumptions and results as it runs, using `assert`/`fail` tasks, and stops with a specific message when something is wrong. For example:

- `lxc-jellyfin.yml` checks for conflicting gids, confirms its data paths are real bind mounts, tests write access as the service account, and waits for `/health`
- `edge-router.yml` fails if Tailscale isn't connected, and asserts the subnet router settings actually applied
- `lxc-baseline.yml` validates the sshd config and removes its drop-in if it broke it

Linting (`yamllint`, `ansible-lint`, Terraform checks) still runs in pre-commit and CI.

### Consequences

Pros

- Checks run every time the playbook does, so they can't be forgotten
- Failures point at the actual problem instead of a later symptom

Cons

- Still testing against live servers, as with ADR 0005
- Playbooks get longer
