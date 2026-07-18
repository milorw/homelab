## Github Workflows

`CI.yml` defines a workflow to run on opened/updated pull requests which target `main`, or on pushes directly to `main`.

### Workflow Job: Lint
The `lint` job is designed to do 3 things:
1. Scan the repository for any secrets (`Gitleaks`)
2. Lint all YAML files (`yamllint`)
3. Lint Ansible-specific files (`ansible-lint`)

It begins by cloning the repo ***using a fetch-depth of 0*** so Gitleaks can scan the full commit history, then runs the scan and passes in the `GITHUB_TOKEN` so Gitleaks can access Github's API for reporting.

Next, it installs Python (`3.12`), then `yamllint` and `ansible-lint` via pip (and caches the install for reuse).

It then runs `yamllint` against `inventory`, `playbooks`, and `roles` directories, and `ansible-lint` against the `playbooks` directory.
