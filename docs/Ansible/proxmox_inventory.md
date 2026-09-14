## Ansible Inventory

Ansible is set up with two inventory files, one static file (`proxmox-hosts.yml`) for individual Proxmox nodes, and one dynamic file (`pve.proxmox.yml`) for Proxmox LXCs/VMs. This setup allows for a constant link to my Proxmox node for API/SSH access, and a dynamically updated list of the current LXCs on the node.

### Filtering & Groups
*example tag list: `lxc`, `role_docker`, `terraform`*

Hosts are filtered:
- must have the `terraform` tag to be included

and then grouped in several ways:
- added to "raw" groups of each existing tag as-is
- added to a specific `role_service` group, cut to just the `service` name
- added to a `type_[lxc/qemu]` (LXC vs full VM)

Lastly, hosts have their full IP (`192.168.68.1/24`) stripped of their mask (`192.168.68.1`), to allow Ansible to actually connect to them.
