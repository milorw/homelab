## Minecraft (Crafty Controller)

A Paper Minecraft server on LXC 110, managed through [Crafty Controller](https://craftycontrol.com) running in Docker - see [ADR 0018](../adr/0018-crafty-controller-for-minecraft.md). Container by [`terraform/lxc-minecraft.tf`](../../terraform/lxc-minecraft.tf), everything inside by [`ansible/playbooks/lxc-minecraft.yml`](../../ansible/playbooks/lxc-minecraft.yml).

```bash
cd ansible
ansible-playbook playbooks/lxc-minecraft.yml
```

### What the playbook does

1. Installs the pinned Java runtime (`openjdk-25-jre-headless`) and checks the JVM actually exists at `java_home`, rather than trusting the package name.
2. Installs Docker (`tasks/docker.yml`).
3. Creates Crafty's directories, renders `templates/apps/crafty.compose.yaml.j2`, and brings Crafty up.
4. Prints the next steps for setting up the server in Crafty's web UI.

The server itself is **not** created by Ansible. On first run:

1. Log in with the generated admin credentials in `/srv/appdata/crafty/config/default-creds.txt`, and set up the admin account.
2. Create a Paper server with the values the playbook prints: version `paper_version`, build `paper_build`, port `service_ports.minecraft`, heap `heap`, and Java path `<java_home>/bin/java`.

Crafty keeps the server's config in its own database, so it isn't in this repo.

### Storage

The world needs SSD speed, but the SSD is the host's boot drive, so **only world data goes there**. Crafty keeps world data entirely under `/crafty/servers`, which makes the split clean:

| Container path | LXC path | Backing |
|---|---|---|
| `/crafty/servers` | `/srv/minecraft/servers` | SSD (`/ssd/minecraft` on the host) |
| `/crafty/app/config` | `/srv/appdata/crafty/config` | `tank/appdata` |
| `/crafty/logs` | `/srv/appdata/crafty/logs` | `tank/appdata` |
| `/crafty/import` | `/srv/appdata/crafty/import` | `tank/appdata` |
| `/crafty/backups` | `/srv/appdata/crafty/backups` | `tank/appdata` |

Both are host bind mounts, so they survive an LXC rebuild. vzdump skips bind mounts, so the SSD world data isn't covered by Proxmox backups.

### Java

Crafty's image only bundles Java 8, 11 and 17. Java 25 is installed on the LXC and bind-mounted read-only into the container at the same path, so it can be picked as the server's Java path in the web UI.

`java_major: 25` and `java_home` (`/usr/lib/jvm/java-25-openjdk-amd64`) were confirmed against the live LXC. Java 21 has been removed; a future Java bump will need its own step to remove the old version.

`paper_version` / `paper_build` (`26.2` / `120`) were confirmed from the live server's own startup log. `heap` is `4G`, kept below the LXC's 6 GB so the JVM, Crafty and Docker all have room.

### Access

| What | How |
|---|---|
| Game | `minecraft.<domain>`, forwarded by HAProxy on the edge router (`service_ports.minecraft`, 25565) |
| Crafty web panel | `mcpanel.milorw.me`, through Caddy (`service_ports.crafty`, 8443). Crafty serves its own self-signed HTTPS, so the edge entry uses `tls_insecure_skip_verify` and passes the original `Host` header. |

See [edge-router.md](edge-router.md).
