resource "proxmox_virtual_environment_container" "minecraft" {
  node_name     = var.pve_node
  vm_id         = 110
  unprivileged  = false
  start_on_boot = true
  started       = true

  tags = ["terraform", "lxc", "role_minecraft"]

  cpu {
    cores = 4
  }

  memory {
    dedicated = 6144
    swap      = 2048
  }

  features {
    keyctl  = true
    nesting = true
  }

  initialization {
    hostname = "minecraft.local"

    ip_config {
      ipv4 {
        address = local.lxc_ips.minecraft
        gateway = local.network.gateway
      }
    }

    dns {
      domain  = local.network.domain
      servers = local.network.dns_servers
    }

    # Without this the container is created with no authorized key and
    # Ansible can't reach it at all.
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
    size         = 16
  }

  network_interface {
    name        = "eth0"
    bridge      = local.network.bridge
    firewall    = true
    mac_address = "BC:24:11:2F:EE:D7"
  }

  # Host bind mount on SSD, not an LXC-owned volume - survives a rebuild.
  # World data ONLY: this is the host's boot drive, so nothing else goes
  # here. Crafty keeps world data entirely under /crafty/servers.
  mount_point {
    volume = local.storage.ssd_minecraft
    path   = "/srv/minecraft"
  }

  # Everything else Crafty needs to persist but not to be fast: its config
  # (SQLite DB, users, server definitions), logs, import staging and
  # backups. Keeps the boot SSD free of anything but world data.
  mount_point {
    volume = local.storage.tank_appdata
    path   = "/srv/appdata"
  }

  lifecycle {
    prevent_destroy = false
    ignore_changes  = [operating_system[0].template_file_id]
  }
}
