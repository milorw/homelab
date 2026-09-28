# Jellyfin media server.

resource "proxmox_virtual_environment_container" "jellyfin" {
  node_name = var.pve_node
  vm_id     = 106

  # Privileged, so uid/gid inside match the host and the jellyfin service
  # account can read /tank/jellyfin (owned by gid 1060) with no mapping.
  unprivileged  = false
  start_on_boot = true
  started       = true

  description = "Jellyfin media server. Managed by Terraform + Ansible (playbooks/lxc-jellyfin.yml)."

  tags = ["terraform", "lxc", "role_jellyfin"]

  cpu {
    cores = 2
  }

  memory {
    dedicated = 3072
    swap      = 1024
  }

  features {
    keyctl  = true
    nesting = true
  }

  initialization {
    hostname = "jellyfin.local"

    ip_config {
      ipv4 {
        address = local.lxc_ips.jellyfin
        gateway = local.network.gateway
      }
    }

    dns {
      domain  = local.network.domain
      servers = local.network.dns_servers
    }

    user_account {
      keys = [trimspace(var.proxmox_ssh_public_key)]
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.6-1_amd64.tar.zst"
    type             = "debian"
  }

  disk {
    datastore_id = "local-lvm"
    size         = 36
  }

  network_interface {
    name     = "eth0"
    bridge   = local.network.bridge
    firewall = true
  }

  # Intel iGPU for VAAPI hardware transcoding. renderD128 does the actual
  # encode/decode; card0 is the KMS node ffmpeg opens alongside it.

  device_passthrough {
    path = "/dev/dri/renderD128"
    gid  = 1061
  }

  device_passthrough {
    path = "/dev/dri/card0"
    gid  = 44
  }

  # Media library. Don't move the path - library paths in the database are absolute.
  mount_point {
    volume = local.storage.tank_jellyfin
    path   = "/opt/jellyfin"
  }

  # Config and library database, mounted onto Jellyfin's own default paths.

  # Only its own data, not all of /tank/appdata.

  mount_point {
    volume = "${local.storage.tank_appdata}/jellyfin_data/data"
    path   = "/var/lib/jellyfin"
  }

  mount_point {
    volume = "${local.storage.tank_appdata}/jellyfin_data/config"
    path   = "/etc/jellyfin"
  }

  lifecycle {
    prevent_destroy = false
    ignore_changes  = [operating_system[0].template_file_id]
  }
}
