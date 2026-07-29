## Ansible Inventory

Ansible is set up with two inventory files, one static file (`proxmox-hosts.yml`) for individual Proxmox nodes, and one dynamic file (`pve.proxmox.yml`) for Proxmox LXCs/VMs. This setup allows for a constant link to my Proxmox node for API/SSH access, and a dynamically updated list of the current LXCs on the node.
