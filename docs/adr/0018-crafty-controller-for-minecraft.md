## Run Minecraft Under Crafty Controller

### Context

Minecraft previously ran as a PaperMC `minecraft.service` systemd unit, managed directly by `lxc-minecraft.yml`. The server's world data needs SSD speed, but the SSD is the host's boot drive, so only world data should live there.

### Decision

Run [Crafty Controller](https://craftycontrol.com) in Docker on the minecraft LXC, deployed from `templates/apps/crafty.compose.yaml.j2`. World data (`/crafty/servers`) is bind-mounted from the SSD, and Crafty's config, logs, imports and backups from the HDD pool. Crafty only bundles Java 8/11/17, so the host's pinned Java install is bind-mounted read-only for it to use. The web panel is exposed through the edge router as `mcpanel`, and the game port still goes through HAProxy (see ADR 0009).

### Consequences

Pros

- Server management (versions, backups, console) through a web UI
- Clean SSD/HDD split along Crafty's own directory layout

Cons

- Initial server setup (admin account, Paper server) is manual, in the web UI
- Server config lives in Crafty's own state, not in this repo
- Java is still installed and pinned on the LXC itself
