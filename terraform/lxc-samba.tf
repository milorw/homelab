resource "proxmox_virtual_environment_container" "samba" {
  node_name     = var.pve_node
  vm_id         = 100
  unprivileged  = false
  start_on_boot = true
  started       = true

  tags = ["terraform", "lxc", "role_samba"]

  cpu {
    cores = 2
  }

  memory {
    dedicated = 2048
    swap      = 1024
  }

  features {
    keyctl  = true
    nesting = true
  }

  initialization {
    hostname = "smb.local"

    ip_config {
      ipv4 {
        address = local.lxc_ips.samba
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
    size         = 8
  }

  network_interface {
    name        = "eth0"
    bridge      = local.network.bridge
    firewall    = true
    mac_address = "bc:24:11:32:aa:5a"
  }

  device_passthrough {
    path = "/dev/net/tun"
  }

  # Order here becomes mp0, mp1, mp2... Keep /tank/shares first -
  # the jellyfin/owen/common/mrw mounts nest inside it.
  mount_point {
    volume = local.storage.tank_shares
    path   = "/srv/shares"
  }
  mount_point {
    volume = local.storage.tank_jellyfin
    path   = "/srv/shares/jellyfin"
  }
  mount_point {
    volume = local.storage.tank_shares_owen
    path   = "/srv/shares/owen"
  }
  mount_point {
    volume = local.storage.tank_shares_common
    path   = "/srv/shares/common"
  }
  mount_point {
    volume = local.storage.tank_shares_mrw
    path   = "/srv/shares/mrw"
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [operating_system[0].template_file_id]
  }
}
