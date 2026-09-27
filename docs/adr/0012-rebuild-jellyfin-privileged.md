## Rebuild Jellyfin as a Privileged LXC Instead of Importing It

### Context

Jellyfin (`192.168.68.97`) was created by a community helper script, outside this repo, as an unprivileged container with a hand-written `lxc.idmap` passing GID 1060 (`jellyfin_srv`) through unmapped so it could read `/tank/jellyfin`. The bpg Terraform provider has no field for `lxc.idmap`, so an import could never describe that container faithfully.

### Decision

Rebuild it as a privileged container (`terraform/lxc-jellyfin.tf`, VM 106) instead of importing it, matching how samba solves the same problem - uid/gid inside the container are the same numbers on the host, so no mapping is needed. Library data moves from the container rootfs to `/tank/appdata/jellyfin_data`, bind-mounted onto Jellyfin's own default paths (`/var/lib/jellyfin`, `/etc/jellyfin`) because Jellyfin stores absolute paths to its data directory in its database. Everything inside the container is managed by `ansible/playbooks/lxc-jellyfin.yml`.

### Consequences

Pros

- Jellyfin is fully described by Terraform + Ansible, like every other LXC
- Library data lives on the pool and survives a container rebuild
- The edge router resolves it from inventory instead of a literal IP

Cons

- Privileged container, so less isolation from the host
- Service account ids have to be pinned by hand (see ADR 0013)
- Files written by the old unprivileged container were owned by an idmap-shifted uid and needed a one-off ownership fix
