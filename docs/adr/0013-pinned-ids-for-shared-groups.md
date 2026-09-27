## Pin UIDs/GIDs Shared Across Containers

### Context

Privileged containers see the host's real uid/gid numbers, so any account that owns data on `/tank` (or a GPU device node) has to have the same id everywhere that data is touched. Samba and Jellyfin both touch the same data: `/tank/jellyfin` is owned by group 1060 (`jellyfin_srv`), and samba's user files by the users' own ids.

Debian allocates system users and groups dynamically (system groups count down from 999), so an unpinned install gets whatever id is free - and then doesn't own its own files. On the Jellyfin image this put `kvm` on 993 and `render` on 992, so pinning the GPU node to the host's `render` gid made it owned by `kvm` inside the container.

### Decision

Pin every id that crosses a container boundary, and create the account before the package that would otherwise create it.

- Samba's users (`mrw` 1000, `owen` 1001) and groups are pinned in `group_vars/samba.yml` to the ids that already own the data on `/tank`.
- Groups shared between containers use a hand-picked range that nothing allocates automatically (1050 `nas_shared`, 1060 `jellyfin_srv`, 1061 `jellyfin_render`), rather than reusing Debian's same-named dynamic groups.
- Jellyfin's own account is pinned to the ids its existing library was owned by (`107:110`).
- Static Debian allocations (e.g. `video` = 44) are kept as-is.

### Consequences

Pros

- Ownership on `/tank` and on device nodes stays correct across rebuilds and base image changes
- Samba and Jellyfin agree on who owns the shared media
- Playbooks can check for a conflicting id and fail with a clear message

Cons

- Ids are hand-managed, and have to be kept in sync between Terraform (`device_passthrough` gids) and group_vars
- A new shared group needs a free id picked from the range by hand
