## Adding a New Service

A service touches up to four layers, depending on what it needs.

1. **Terraform** - only if the service needs its own LXC.
2. **Service catalog** - one entry in `group_vars/all/services.yml`: its port, where it runs, and how it's exposed.
3. **Ansible: deploy the service** - the compose file/systemd unit, secrets, the playbook itself.
4. **Apply** - run the playbooks, so the edge router and homepage pick it up.

If you're adding a service to an LXC that already exists (e.g. another docker-compose app on `docker_apps`), skip straight to step 2.

---

### 1. Terraform (new LXC only)

Files: `terraform/lxc-<name>.tf`, `terraform/locals.tf`.

- [ ] Add an IP to `locals.network` → `lxc_ips.<name>` in `locals.tf`.
- [ ] If the LXC needs a host path shared with another LXC, or just want it named for visibility: add it to `locals.storage`. Reference it from `mount_point { volume = local.storage.<name> }`, don't write the literal path twice.
- [ ] Write `lxc-<name>.tf`: `tags = ["terraform", "lxc", "role_<name>"]` - the `role_<name>` tag is what makes Ansible's dynamic inventory create a group called `<name>` for it (see `ansible/inventory/pve.proxmox.yml`'s `keyed_groups`). Get this right or nothing downstream can find the host.
- [ ] `initialization { ip_config { ... gateway = local.network.gateway } dns { domain = local.network.domain; servers = local.network.dns_servers } }`.
- [ ] `unprivileged`/`features`: containers with host bind mounts (`mount_point` pointing at a real host path) are privileged (`unprivileged = false`), so uid/gid inside match the host with no mapping - see `lxc-samba.tf` or `lxc-jellyfin.tf`. The bpg provider has no field for `lxc.idmap`, so an unprivileged container with bind mounts can't be described here (see `docs/adr/0012-rebuild-jellyfin-privileged.md`). Any ids that own data on the host have to be pinned (see `docs/adr/0013-pinned-ids-for-shared-groups.md`). Containers with no bind mounts (just a local-lvm disk, like the edge router) can stay unprivileged. Docker needs `nesting = true` either way.
- [ ] Only mount `/tank/appdata` (or similar persistent host storage) if the service has real data that can't be lost. Don't mount a host path just to hold compose files/config - Ansible re-renders those from this repo, they don't need to survive independent of the LXC. (See `docs/adr/0011-edge-router-docker-compose.md` for why the edge router has no persistent mounts at all.)
- [ ] `terraform fmt && terraform validate` in `terraform/`. Actually applying it is a separate, deliberate step - don't run `terraform apply` as part of writing the config.

### 2. Service catalog

File: `ansible/inventory/group_vars/all/services.yml` - see `docs/adr/0021-service-catalog.md`. Every other file that needs to know about a service (port registry, edge router, homepage) is generated from this entry, so this is the only place to register it.

- [ ] Add an entry under `services`, keyed by the service's name. Where it goes in the list is where it appears on the homepage.
- [ ] `port`: the port the service listens on, on its host. Everything else references it as `{{ service_ports.<name> }}` - the compose template, `.env` templates, playbooks - so it's only ever written here.
- [ ] `host`: the inventory group it runs on (`docker_apps`, `jellyfin`, the `role_<name>` group from step 1, ...). The edge router looks up its address from the inventory. For something this repo doesn't manage (Home Assistant, an external NAS), use `address: <ip>` instead.
- [ ] `domains`: every domain it should be reachable under, e.g. `[milorw.me, owennwb.com]`. Leave it out if it shouldn't get a hostname at all.
- [ ] How the edge router serves it - pick one:
  - `proxy: {encodings: [gzip, zstd]}` for HTTP (almost everything), through Caddy. If the backend is HTTPS-only with a self-signed cert (like Proxmox), add `transport_http: [tls_insecure_skip_verify]` (a list) - see the `proxmox` entry and `docs/Ansible/edge-router.md` for why that exact syntax. `headers` is passed through too (see `crafty`).
  - `tcp: true` for anything that isn't HTTP (Minecraft's protocol, for example), forwarded by HAProxy on the same port - see `docs/adr/0009-haproxy-for-tcp-services.md`.
- [ ] `subdomain`: only if it should be served under a different name than its key (`crafty` is served as `mcpanel`).
- [ ] `homepage: {name, icon, description, group}`: how it looks on the homepage. Optional - without it, it gets a capitalized name, `<name>.png` as the icon, and the Services group. It only appears on the homepage at all if its `domains` include every domain (see `docs/adr/0014-homepage-generated-from-edge-router.md`). A widget instead of a plain link goes in `homepage_widgets` in `group_vars/docker_apps.yml`.
- [ ] `container`: its container name, if it runs on `docker_apps` - for the homepage's status dot. Compose names containers `<project>-<service>-1` unless the compose file sets `container_name`.
- [ ] `firewall`: which sources may reach `port` on its host (`edge_router`, `lan_net`, `ts_net`). Recorded, but not wired up yet.

### 3. Ansible: deploy the service

Files: `ansible/playbooks/<playbook>.yml`, `ansible/playbooks/templates/...`, `ansible/playbooks/files/...`, `ansible/inventory/group_vars/<group>.yml`.

- [ ] If this is a new LXC/group: new `ansible/inventory/group_vars/<name>.yml` for its config, new `ansible/playbooks/<name>.yml` playbook (`hosts: <name>`, matching the inventory group from the terraform tag). Look at `edge-router.yml` or `docker-apps.yml` as a starting template.
- [ ] If it's docker-compose based: decide static file vs. Jinja template.
  - No secrets, no values another file needs to share (a port, say) → static file under `ansible/playbooks/files/apps/<name>/compose.yaml` (or wherever the playbook's files live), deployed with `ansible.builtin.copy`.
  - Has a port that the edge router also needs to know, or other host-specific values → `ansible/playbooks/templates/apps/<name>.compose.yaml.j2`, deployed with `ansible.builtin.template`. See `templates/apps/homebox.compose.yaml.j2` for the pattern - only the values that need to vary get templated, the rest stays plain YAML.
  - Has secrets → keep the compose file's `${VAR}` references, and add a `<name>.env.j2` template that renders them from vault-backed vars (next bullet). Docker Compose reads `.env` next to the compose file automatically - you don't need to template the whole compose file just because it has secrets (see `sure.env.j2` + the static `sure/compose.yaml`).
- [ ] Outbound email: use the shared relay settings in `group_vars/all/smtp.yml` (`smtp_host`, `smtp_user`, etc.) in the app's `.env.j2` rather than adding new ones - see `mealie.env.j2` and `docs/adr/0017-shared-smtp-relay.md`.
- [ ] Secrets: add vault-indirection vars to the group_vars file (`thing: "{{ vault_thing }}"`, matching every other secret in this repo), template them into the rendered `.env` (`mode: "0600"`, `no_log: true` on the templating task), and tell the user the exact `vault_*` variable names to add via `ansible-vault edit ansible/inventory/group_vars/all/vault.yml` - don't add them yourself.
- [ ] Playbook tasks: create the app's directory, deploy compose file, render `.env` if needed (`notify: Recreate <name>`), bring up with `community.docker.docker_compose_v2` (`state: present`). Add a `Recreate <name>` handler (`recreate: always`) so config changes actually take effect - `state: present` alone won't recreate a running container just because its source file changed.
- [ ] Non-docker services (apt packages, systemd units, etc.): follow `lxc-jellyfin.yml`'s pattern - if the service account owns data on the host, create it with pinned ids *before* installing the package (so the package adopts it instead of picking its own), only template config files the app never rewrites itself, use systemd drop-ins rather than replacing the packaged unit, and restart via handlers. Check the result in the play itself (`assert`/`fail`) - see `docs/adr/0020-in-playbook-validation.md`.
- [ ] Verify before considering it done: `yamllint` the new files, `ansible-playbook <playbook> --syntax-check`, and actually render any new Jinja templates against representative vars before trusting them - a throwaway play does this without touching real infra:

  ```yaml
  # /tmp/render_check.yml
  - hosts: localhost
    gather_facts: false
    connection: local
    vars_files:
      - /path/to/ansible/inventory/group_vars/<name>.yml
    vars:
      # anything the group_vars file needs that only exists at runtime
      # (vault_* secrets, ansible_host, etc.) - fake values are fine here
    tasks:
      - ansible.builtin.template:
          src: /path/to/template.j2
          dest: /tmp/rendered.out
  ```

  `ansible-playbook -i localhost, /tmp/render_check.yml`, then read `/tmp/rendered.out`. Delete the throwaway files afterward.

### 4. Apply

- [ ] Re-run `edge-router.yml` (it re-renders `Corefile`/`Caddyfile`/`haproxy.cfg`, restarts CoreDNS/HAProxy if their config changed, and reloads Caddy - no manual restart needed). The service gets the edge router's error pages automatically.
- [ ] Then run the service's own playbook. If the service is on every domain, run `docker-apps.yml` too, so the homepage lists it - after the edge router, so its link works straight away.

---

### Worked example

Adding a hypothetical `foo` app to the existing `docker_apps` LXC, reachable at `foo.<domain>` on both domains, no secrets:

1. `ansible/inventory/group_vars/all/services.yml`:

   ```yaml
   foo:
     host: docker_apps
     port: 8080
     domains: [milorw.me, owennwb.com]
     proxy: {encodings: [gzip, zstd]}
     homepage: {name: Foo, icon: foo.png, description: Does foo things, group: Home}
     container: foo
     firewall: [edge_router]
   ```

2. `ansible/playbooks/templates/apps/foo.compose.yaml.j2`: compose file with `container_name: foo` and `ports: ["{{ service_ports.foo }}:8080"]`.
3. `ansible/playbooks/docker-apps.yml`: add the directory-creation loop entry, a "Render foo compose file" task (`notify: Recreate foo`), a "Bring up foo" task, and a `Recreate foo` handler.
4. Run `edge-router.yml`, then `docker-apps.yml`.

No Terraform changes needed - `docker_apps` already exists.

---

### Quick reference: "I need to add X, what do I touch?"

| Need | Files |
|---|---|
| A brand-new LXC | `terraform/lxc-<name>.tf`, `terraform/locals.tf` |
| A new persistent host storage path | `terraform/locals.tf` (`storage`), the LXC's `mount_point` |
| A docker-compose app on an existing LXC | that LXC's playbook + `templates/apps/` or `files/apps/` |
| Secrets for a service | group_vars indirection vars + `.env.j2` template + tell the user the `vault_*` names |
| A service's port, hostname, proxy route or homepage entry | its entry in `ansible/inventory/group_vars/all/services.yml` |
| A new domain | `edge_domain_settings` in `ansible/inventory/group_vars/edge_router.yml`, then add it to services' `domains` |
| A homepage widget | `homepage_widgets` in `group_vars/docker_apps.yml` |
| Outbound email | `group_vars/all/smtp.yml` vars in the app's `.env.j2` |
| An IP that's already Terraform-managed | dynamic inventory lookup (`hostvars[groups['<name>'][0]].ansible_host`), not a literal |
| A setting every LXC should have | `ansible/playbooks/lxc-baseline.yml` + `group_vars/proxmox_all_lxc.yml` |
