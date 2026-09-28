## Package Updates

[`ansible/playbooks/update-packages.yml`](../../ansible/playbooks/update-packages.yml) applies apt updates to every LXC, then the Proxmox host. The shared steps are in `playbooks/tasks/package-updates.yml`.

```bash
cd ansible
ansible-playbook playbooks/update-packages.yml --check      # preview: lists what would update, changes nothing
ansible-playbook playbooks/update-packages.yml              # security updates only
ansible-playbook playbooks/update-packages.yml -e update_scope=all
ansible-playbook playbooks/update-packages.yml --limit jellyfin
```

### What gets updated

- `update_scope: security` (default) - only packages offered from a Debian `*-security` suite. The Proxmox kernel and PVE packages come from Proxmox's own repo, not a security suite, so they're **not** included - use `all` for those.
- `update_scope: all` - everything. LXCs use `apt upgrade` (`safe`: never removes packages). The host uses `dist-upgrade`, which Proxmox requires - a plain upgrade can leave PVE half-updated.

### Why it won't silently break everything

- **One LXC at a time, and the run stops at the first failure** (`serial: 1`, `max_fail_percentage: 0`). A bad update stops on the container it broke, and the rest are untouched.
- **Backup first.** Before updating an LXC, it takes a vzdump backup of it to `tank-backup`, and keeps only the newest one per container, identified by its notes (`update-packages pre-update`), so manual backups are never touched. If the backup fails, that container isn't updated. Only the container's own disk is backed up - bind mounts (`/tank`, the SSD) are left out, so restoring never touches app data. It's a backup rather than a snapshot because `pct snapshot` refuses any container with bind mounts. Turn it off with `-e update_backup=false`. These backups don't send Proxmox's backup notification email (other backups still do).
- **Checked afterwards.** It records failed systemd units and running Docker containers before updating, and fails if any new unit has failed or any container hasn't come back within a minute. Something that was already down doesn't count.
- **The host goes last**, after every LXC has succeeded, with the same checks but no backup.
- **No immediate reboots.** See below.

Conffile prompts can't block it: apt keeps the existing config file and installs the package's version alongside it.

### Host reboots

LXCs share the host's kernel, so they never need a reboot for updates. The host does when a new kernel is installed. Debian and Proxmox don't create `/run/reboot-required`, so the play compares the running kernel with the newest one in `/boot`.

If they differ, it schedules a **one-off reboot** at `update_reboot_time` (05:00 by default, after the 04:00 minecraft backup). The reboot waits until that time rather than happening straight away, since it stops every guest. It's a transient systemd timer, which lives only in memory, so:

- rebooting the host yourself before then clears it - it won't fire afterwards
- it can't turn into a nightly restart - the reboot it triggers removes it
- it only gets scheduled if the whole run succeeded, since a failure stops the playbook before the host play

```bash
systemctl list-timers update-reboot.timer    # is one scheduled?
systemctl stop update-reboot.timer           # cancel it
```

`-e update_schedule_reboot=false` just reports that a reboot is needed.

### If an update breaks a container

Restore its pre-update backup - from the web UI (the container's **Backup** tab, the one with notes `update-packages pre-update`), or on the host:

```bash
pvesh get /nodes/localhost/storage/tank-backup/content --content backup --vmid <vmid>   # find the volid
pct stop <vmid>
pct restore <vmid> <volid> --force
pct start <vmid>
```

The bind mounts stay in the restored config and their data is untouched, so the app picks up where it left off.

### Worth knowing

- A patched library isn't used by a service until that service restarts. Package upgrades restart their own services, but other long-running processes (e.g. inside Docker containers) keep the old copy until they restart.
- Docker images are not updated by this - it only covers the containers' own OS packages.
