resource "proxmox_virtual_environment_container" "edge_router" {
  node_name     = var.pve_node
  vm_id         = 105
  unprivileged  = true
  start_on_boot = true
  started       = true

  tags = ["terraform", "lxc", "role_edge_router"]

  cpu {
    cores = 2
  }

  memory {
    dedicated = 1024
    swap      = 512
  }

  features {
    keyctl  = true
    nesting = true
  }

  initialization {
    hostname = "edge"

    ip_config {
      ipv4 {
        address = local.lxc_ips.edge_router
        gateway = local.network.gateway
      }
    }

    dns {
      domain  = local.network.domain
      servers = local.network.dns_servers
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.6-1_amd64.tar.zst"
    type             = "debian"
  }

  disk {
    datastore_id = "local-lvm"
    size         = 10
  }

  network_interface {
    name        = "eth0"
    bridge      = local.network.bridge
    firewall    = true
    mac_address = "BC:24:11:AB:EF:75"
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [operating_system[0].template_file_id]
  }
}
