## Github Workflows

`.github/workflows/ci.yml` defines a workflow to run on opened/updated pull requests which target `main`, or on pushes directly to `main`. It has two jobs, `lint` and `terraform`.

### Workflow Job: Lint
The `lint` job is designed to do 3 things:
1. Scan the repository for any secrets (`Gitleaks`)
2. Lint all YAML files (`yamllint`)
3. Lint Ansible-specific files (`ansible-lint`)

It begins by cloning the repo ***using a fetch-depth of 0*** so Gitleaks can scan the full commit history, then runs the scan and passes in the `GITHUB_TOKEN` so Gitleaks can access Github's API for reporting.

Next, it installs Python (`3.12`), then `yamllint` and `ansible-lint` via pip from `.github/requirements-lint.txt` (and caches the install for reuse). It also installs the Ansible collections the playbooks use from `.github/requirements.yml` (`community.proxmox`, `community.general`, `community.docker`), so `ansible-lint` can resolve their modules.

It then runs `yamllint` against the `ansible/inventory` and `ansible/playbooks` directories, and `ansible-lint` against the `ansible/playbooks` directory.

The vault password isn't available in CI, so Ansible runs with the vault disabled - see [ADR 0006](../adr/0006-ansible-vault.md).

### Workflow Job: Terraform
The `terraform` job checks the files in `terraform/`:
1. `terraform fmt -check` - formatting
2. `terraform init -backend=false` then `terraform validate` - config is valid, without needing state or Proxmox access
3. `tflint` - Terraform linting
