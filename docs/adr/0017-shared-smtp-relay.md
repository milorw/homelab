## Shared SMTP Relay Settings in `group_vars/all`

### Context

Mealie needs outbound email, and other apps (and host alerting) will too. Giving each app its own copy of the relay settings would mean several places to update when credentials rotate.

### Decision

Define the outbound relay (Azure Communication Services, STARTTLS on 587) once in `ansible/inventory/group_vars/all/smtp.yml`, with credentials pulled from the vault (`vault_smtp_from_email`, `vault_smtp_user`, `vault_smtp_password`). Apps reference `smtp_*` vars from their `.env` templates.

### Consequences

Pros

- One place to change relay settings or rotate credentials
- Visible to every host and group, so any playbook can use it

Cons

- Every app shares one sending identity and credential
