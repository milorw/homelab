## Terraform LXC Layout

Terraform is set up to have one infrastructure config file (`locals.tf`), and a separate file for each LXC. See [ADR 0008](../adr/0008-shared-terraform-locals.md).

### locals.tf

`locals.tf` contains several infrastructure variable blocks:

- `network` - default network connection details (gateway, bridge, DNS servers and search domain)

- `lxc_ips` - list of unique ips for each LXC

- `storage` - list of proxmox storage paths, mostly datasets on `tank`, plus `ssd_minecraft` - a plain host directory on the SSD for Minecraft's world data

This allows for variable substitution inside of each LXC's file, such as:

```
ipv4 {
address = local.lxc_ips.docker_apps
gateway = local.network.gateway
}
```

### LXC files

Each LXC gets its own setup file (`lxc-<name>.tf`), with any custom configuration set in that file rather than being pulled from `locals.tf`.

Every LXC is tagged `["terraform", "lxc", "role_<name>"]`. The `terraform` tag is what puts it in Ansible's inventory at all, and `role_<name>` becomes its Ansible group - see [proxmox_inventory.md](../Ansible/proxmox_inventory.md).

| File | ID | Privileged | Notes |
|---|---|---|---|
| `lxc-samba.tf` | 100 | yes | bind mounts the `tank` shares and the Jellyfin media |
| `lxc-apps.tf` | 104 | yes | Docker host for the `docker_apps` services; bind mounts `tank/appdata` and mrw's share |
| `lxc-edge-router.tf` | 105 | no | no persistent mounts - see [ADR 0011](../adr/0011-edge-router-docker-compose.md) |
| `lxc-jellyfin.tf` | 106 | yes | GPU passthrough, and bind mounts for media and library data - see [ADR 0012](../adr/0012-rebuild-jellyfin-privileged.md) |
| `lxc-minecraft.tf` | 110 | yes | world data on the SSD, everything else on `tank` |
