## Docker Apps

LXC 104 runs the smaller web apps as separate Docker Compose projects. Container by [`terraform/lxc-apps.tf`](../../terraform/lxc-apps.tf), everything inside by [`ansible/playbooks/docker-apps.yml`](../../ansible/playbooks/docker-apps.yml), with its vars in `ansible/inventory/group_vars/docker_apps.yml`.

```bash
cd ansible
ansible-playbook playbooks/docker-apps.yml
```

| App | What it is | Port | Data |
|---|---|---|---|
| homebox | Home inventory | 3100 | `/srv/appdata/homebox_data` |
| ombi | Media requests | 3579 | `/srv/appdata/ombi_data` |
| sure | Personal finance (Rails + Postgres + Redis + Sidekiq) | 3000 | `/srv/appdata/sure_data` |
| mealie | Recipes | 9925 | `/srv/appdata/mealie_data` |
| homepage | Dashboard of every service | 3010 | none - config is fully rendered by Ansible |

Ports come from `group_vars/all/service_ports.yml`, shared with the edge router. `/srv/appdata` is `tank/appdata` on the host, so app data survives an LXC rebuild.

### Layout

Each app gets `/opt/apps/<app>/` with its `compose.yaml` and, if it has secrets, a `.env` (`0600`). The compose file is either:

- a **template** (`templates/apps/<app>.compose.yaml.j2`) when it needs values from this repo, like its port, or
- a **static file** (`files/apps/<app>/compose.yaml`) when it doesn't - sure's, which only reads `${VAR}`s from its `.env`.

Any change to an app's compose file or `.env` triggers a `Recreate <app>` handler. `state: present` alone won't recreate a running container just because its config changed.

### sure

**Database password.** Postgres only reads `POSTGRES_USER` / `POSTGRES_PASSWORD` when it first creates its data directory, so changing `vault_sure_postgres_password` never reaches the existing database, and the app can no longer log in. After bringing sure up, the play tries to log in with the vault credentials. Only if that's rejected does it run `templates/apps/sure-role.sql.j2` as the `postgres` superuser, which:

- creates the app's role if it's missing, and sets its password to the vault's
- makes it owner of the database, the `public` schema, and every table, sequence and view in it (the app runs its own migrations, so it has to own what it migrates)

**Encryption keys.** Sure derives its Active Record encryption keys from `SECRET_KEY_BASE` when they aren't set. `sure.env.j2` sets all three to exactly the values sure already derives, so nothing is re-encrypted - but the data stays readable if `SECRET_KEY_BASE` is ever rotated, and sure's startup warning goes away.

### mealie

- Signups are off (`ALLOW_SIGNUP=false`), and `BASE_URL` is `mealie_base_url`.
- Email goes through the shared relay in `group_vars/all/smtp.yml` - see [ADR 0017](../adr/0017-shared-smtp-relay.md).
- **Custom AI prompts.** `files/apps/mealie/prompts/` is copied to `/opt/apps/mealie/prompts/` and mounted read-only into the container, with `OPENAI_CUSTOM_PROMPT_DIR` pointing at it. The prompts are forked from Mealie v3.27.0's built-in ones, to pull ingredient lines out of the steps and combine duplicate ingredients. A custom prompt file **replaces** the built-in one entirely, so they may need re-syncing after a Mealie upgrade changes the originals.

### homepage

The service list is generated from the edge router's config, not maintained by hand - see [ADR 0014](../adr/0014-homepage-generated-from-edge-router.md).

- **Which services appear:** every service listed under **every** domain in `edge_domains` (so each link works on both domains), except homepage itself. Links use `homepage_link_domain`.
- **How they look:** `homepage_service_meta` optionally sets each service's name, icon, description and group. Without an entry, a service gets its capitalized name, `<service>.png` as the icon, and the `Services` group. Groups appear in `homepage_groups` order.
- **Widgets:** a service in `homepage_widgets` shows that widget instead of a link. Currently minecraft (server status) and ombi (request counts, using `vault_ombi_api_key`). Because the API key ends up in `services.yaml`, that file is `0640` and its task is `no_log`.
- **Container status:** `homepage_docker_containers` maps a service to its container name on this LXC, for the status dot. homepage reads the Docker socket read-only. Compose names containers `<project>-<service>-1` unless the compose file sets `container_name`, which is why sure's is `sure-web-1`.
- **Bookmarks:** `homepage_bookmarks` is empty, which also stops homepage filling `bookmarks.yaml` with example links.

`HOMEPAGE_ALLOWED_HOSTS` is also generated: `homepage.<domain>` for each domain that serves it, plus the LXC's own `IP:port`.

Because the service list reads the edge router's vars, run `edge-router.yml` first when adding a service, then `docker-apps.yml`.
