## Jellyfin

Media server on LXC 106, with Intel VAAPI hardware transcoding. Container by [`terraform/lxc-jellyfin.tf`](../../terraform/lxc-jellyfin.tf), everything inside by [`ansible/playbooks/lxc-jellyfin.yml`](../../ansible/playbooks/lxc-jellyfin.yml).

```bash
cd ansible
ansible-playbook playbooks/lxc-jellyfin.yml
```

### Where it came from

Created by a community helper script as an **unprivileged** container with a hand-written `lxc.idmap` that passed GID 1060 (`jellyfin_srv`) through unmapped so it could read `/tank/jellyfin`. The bpg Terraform provider has no field for `lxc.idmap`, so that container could never be described in this repo faithfully.

It was rebuilt **privileged**, matching how samba solves the same problem: uid and gid inside are the same numbers on the host, so no mapping is needed at all. See [ADR 0012](../adr/0012-rebuild-jellyfin-privileged.md).

### Why the ids are pinned

`jellyfin_uid: 107` and `jellyfin_gid: 110` are not cosmetic. Debian allocates system uids dynamically, so an unpinned install picks whatever is free - and then does not own its own library. The playbook therefore **creates the account before installing the package**, so the postinst adopts it rather than inventing one. See [ADR 0013](../adr/0013-pinned-ids-for-shared-groups.md).

| id | What owns it |
|---|---|
| `107:110` | `/tank/appdata/jellyfin_data`, and jellyfin's own files under `/tank/jellyfin` |
| `44` (`video`), `1061` (`jellyfin_render`) | the GPU device nodes - matching the `gid` on each `device_passthrough` in Terraform |
| `1060` (`jellyfin_srv`) | the media on `/tank/jellyfin`, shared with samba |

### Why the render group isn't called `render`

The obvious thing is to pin the device to the host's `render` gid, 993. That fails, and the failure is instructive.

Debian allocates system groups **dynamically, from 999 downward**. On this image it handed 993 to `kvm` and put `render` on 992 - so pinning the device node to 993 makes it owned by `kvm` inside the container, and `groupmod` refuses to renumber `render` onto an id `kvm` already holds:

```
groupmod: GID '993' already exists
```

Chasing whichever number Debian picked (992 today) would work until the base image shifted and then silently break hardware transcoding. So the render node gets **1061**, a dedicated `jellyfin_render` group in the hand-picked range this repo already uses for shared groups - 1050 `nas_shared`, 1060 `jellyfin_srv`. Nothing allocates gids there automatically.

`video` keeps 44 because that one *is* a static allocation from `base-passwd`, not a dynamic one, so it's stable.

The playbook checks this before it tries: if a wanted gid belongs to a different group, it fails naming the group in the way, rather than leaving you with `groupmod`'s message.

### Storage

| Path | Backing | Contents |
|---|---|---|
| `/var/lib/jellyfin` | `/tank/appdata/jellyfin_data/data` | library database, metadata, plugins - ~12 GB |
| `/etc/jellyfin` | `/tank/appdata/jellyfin_data/config` | the XML config and user accounts |
| `/opt/jellyfin` | `/tank/jellyfin` | the media itself |
| `/var/cache/jellyfin`, `/var/log/jellyfin` | container disk | transcode scratch and logs |

### Why the data sits on Jellyfin's default paths

Every other service here mounts `/tank/appdata` somewhere neutral and points the app at it. Jellyfin can't be done that way, and finding out why cost a debugging round.

**Jellyfin writes absolute paths to its own data directory into the database.** The first attempt mounted the pool at `/srv/appdata/jellyfin_data` and redirected `JELLYFIN_DATA_DIR` there. The service started fine, the files were all present, and then every poster 404'd:

```
[ERR] Could not find file '/var/lib/jellyfin/metadata/library/58/…/poster.jpg'
```

**11,259 of 12,388** rows in `BaseItemImageInfos` contained absolute `/var/lib/jellyfin/…` paths. Moving the directory orphaned all of them.

So the bind mounts land on `/var/lib/jellyfin` and `/etc/jellyfin` instead. The data is still on the pool, the stored paths stay valid, and nothing has to be rewritten. The remaining 1,129 artwork rows point into `/opt/jellyfin` - artwork stored next to the media - and were never affected.

Only this service's own data is mounted, not the whole of `/tank/appdata`, so the container can't see other services' state.

The playbook asserts both are real bind mounts via `findmnt` rather than just checking the directories exist - the package creates them either way, and an empty directory on the rootfs would silently rebuild the library and lose it on the next container rebuild.

Cache and logs stay on the container's own disk deliberately: they're rebuildable and write-heavy, and there's no reason to put that churn on the spinning pool.

**The media mount path is load-bearing.** Every library path in Jellyfin's database is absolute, so moving `/opt/jellyfin` somewhere tidier would orphan all five libraries and force a full rescan. It stays where the community script put it.

### What Ansible manages, and what it deliberately doesn't

Managed: the apt repo and key, the package, the service account and its groups, `/etc/default/jellyfin`, and a systemd drop-in.

**Not managed: the XML in `/etc/jellyfin`.** Jellyfin rewrites `encoding.xml`, `network.xml` and `system.xml` whenever a setting changes in the web UI. Templating them would mean Ansible and the UI silently undoing each other's work. `/etc/default/jellyfin` is the exception - Jellyfin only ever reads it, so it's safe to template, and the paths are pinned there explicitly even though they match the package defaults.

For reference, the settings that matter if they ever need restoring by hand:

- `HardwareAccelerationType: vaapi`, `VaapiDevice: /dev/dri/renderD128`, `EnableHardwareEncoding: true`
- `InternalHttpPort: 8096`, HTTPS off (Caddy terminates TLS at the edge router)

### Permissions, and how samba fits

Samba shares the same dataset as `Jellyfin-Media`, and its config is already ideal for this:

```
force group = jellyfin_srv
force create mode = 0664
force directory mode = 2775
```

So anything written over SMB lands in group 1060, group-writable, with the setgid bit carrying the group down the tree. Jellyfin is in that group, so it can read and manage all of it.

Jellyfin's own writes were the asymmetric half. With the default umask it creates `0644` files and `0755` directories, so the artwork and `.trickplay` data it generates alongside the media is **not** writable by the `jellyfin_srv` group - meaning samba users can't manage or delete it. A `UMask=002` systemd drop-in makes jellyfin create `0664`/`0775` and match samba.

One thing worth knowing if this is ever repeated: files the *unprivileged* container wrote were owned by uid `100107` (107 plus the idmap offset), which corresponded to nothing after the rebuild. They were group-readable but not group-writable, so the new service couldn't regenerate or remove them. A one-off task reclaimed them with `find -uid 100107 -exec chown`. It has run, and has been removed from the playbook.

### Verification

The play doesn't assume access, it proves it - using `runuser` to become the service account and test write access to both GPU nodes, the data and config directories and the media, then waits for `/health` to answer on 8096. `runuser` rather than `sudo`, since sudo isn't necessarily installed in a minimal container.
