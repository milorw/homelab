## Local Workflow

This repository has a pre-commit config file to check for secrets and validate file linting on local commits. It first runs `Gitleaks` to scan for any committed secrets, then:

- `ansible-lint`, run with `--project-dir ansible` (the vault file and `.github/` are excluded)
- `terraform_fmt`, `terraform_validate` and `terraform_tflint`, for files in `terraform/`
- `yamllint`

Several pre-commit hooks are also enabled:
- check-added-large-files
- check-case-conflict
- check-merge-conflict
- detect-private-key
- end-of-file-fixer
- mixed-line-ending
- trailing-whitespace

Additionally, there is a `.yamllint` config file which removes line-length limits, disables the file start delimiter check, and forbids implicit/explicit octal values (so file modes have to be quoted strings like `"0644"`).

### direnv

Both `ansible/` and `terraform/` have an `.envrc` for direnv:

- `ansible/.envrc` points `ANSIBLE_VAULT_PASSWORD_FILE` at the 1Password vault script, if it exists - see [ADR 0002](../adr/0002-use-1password-cli.md) and [ADR 0006](../adr/0006-ansible-vault.md).
- `terraform/.envrc` sets the Proxmox provider endpoint and pulls its credentials from 1Password with `op read`.
