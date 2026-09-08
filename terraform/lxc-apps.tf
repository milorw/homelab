resource "proxmox_virtual_environment_container" "docker_apps" {
  node_name     = var.pve_node
  vm_id         = 104
  unprivileged  = false
  start_on_boot = true
  started       = true

  tags = ["terraform", "lxc", "role_docker_apps"]

  cpu {
    cores = 2
  }

  memory {
    dedicated = 4096
    swap      = 2048
  }

  features {
    fuse    = true
    nesting = true
  }

  initialization {
    hostname = "apps"

    ip_config {
      ipv4 {
        address = local.lxc_ips.docker_apps
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
    size         = 50
  }

  network_interface {
    name        = "eth0"
    bridge      = local.network.bridge
    firewall    = true
    mac_address = "BC:24:11:9F:D1:A9"
  }

  mount_point {
    volume = local.storage.tank_shares_mrw
    path   = "/srv/share"
  }

  mount_point {
    volume = local.storage.tank_appdata
    path   = "/srv/appdata"
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [operating_system[0].template_file_id]
  }
}
