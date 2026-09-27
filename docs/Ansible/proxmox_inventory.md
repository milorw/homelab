## Ansible Inventory

Ansible is set up with two inventory files, one static file (`proxmox-hosts.yml`) for individual Proxmox nodes, and one dynamic file (`pve.proxmox.yml`) for Proxmox LXCs/VMs. This setup allows for a constant link to my Proxmox node for API/SSH access, and a dynamically updated list of the current LXCs on the node.

### Filtering & Groups
*example tag list: `lxc`, `role_docker_apps`, `terraform`*

Hosts are filtered:
- must have the `terraform` tag to be included

and then grouped in several ways:
- added to a `tag_<tag>` group for each tag as-is (`tag_terraform`, `tag_lxc`, `tag_role_docker_apps`)
- added to a group named after its `role_` tag, with the prefix cut off (`role_docker_apps` → `docker_apps`). This is the group each playbook targets, and the name its `group_vars/<name>.yml` file uses.
- added to a `type_[lxc/qemu]` (LXC vs full VM)
- added to `proxmox_all_lxc`, which the Proxmox plugin creates by itself for every LXC. `lxc-baseline.yml` targets it, and the edge router builds its Tailscale routes from it.

Lastly, hosts have their full IP (`192.168.68.1/24`) stripped of their mask (`192.168.68.1`), to allow Ansible to actually connect to them.

Other files can look up an LXC's IP from the inventory rather than hardcoding it, e.g. `hostvars[groups['jellyfin'][0]].ansible_host`.
