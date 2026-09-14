## Terraform LXC Layout

Terraform is set up to have one infrastructure config file (`locals.tf`), and a separate file for each LXC.

### locals.tf

`locals.tf` contains several infrastructure variable blocks:

- `network` - default network connection details

- `lxc_ips` - list of unique ips for each LXC

- `storage` - list of proxmox storage paths

This allows for variable substitution inside of each LXC's file, such as:

```
ipv4 {
address = local.lxc_ips.docker_apps
gateway = local.network.gateway
}
```

### LXC files

Each LXC gets its on setup file, with any custom configuration set in that file rather than being pulled from `locals.tf`.
