## Local Workflow

This repository has a pre-commit config file to check for secrets and validate file linting on local commits. It first runs `Gitleaks` to scan for any committed secrets, then uses `yamllint` and `ansible-lint` to validate the files.

Several pre-commit hooks are also enabled:
- check-added-large-files
- check-case-conflict
- check-merge-conflict
- detect-private-key
- end-of-file-fixer
- mixed-line-ending
- trailing-whitespace

Additionally, there is a `.yamllint` config file which removes line-length limits, and disables the file start delimiter check.
