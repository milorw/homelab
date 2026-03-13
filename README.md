## Info

This is the primary storage repository for my Proxmox server, and it holds all of my LXC configs, as well as any scripts used by the host or in specific LXCs/VMs.

The primary access point for my server is the edge router LXC, which uses Cloudflare, Tailscale, and a reverse proxy setup to forward any `service.domain_name` web traffic through Tailscale and into the correct service's IP/port.

There is a second Tailscale instance running on the Proxmox host as a backup connection (only for server admins) if the edge router is not working to allow continued remote access, and only specific devices and services are allowed to communicate through LAN.
