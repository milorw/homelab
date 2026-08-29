locals {
  defaults = {
    cores    = 1
    memory   = 512
    disk     = 8
    template = "local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst"
    start    = true
  }

  # only the per-container differences
  containers_raw = {
  }

  # merge defaults in so each.value always has every key
  containers = {
    for name, cfg in local.containers_raw : name => merge(local.defaults, cfg)
  }
}

resource "proxmox_virtual_environment_container" "lxc" {
  for_each = local.containers

  node_name     = var.pve_node
  vm_id         = each.value.vm_id
  started       = each.value.start
  start_on_boot = true

  tags = ["terraform", "lxc", "role_${each.key}"]

  initialization {
    hostname = each.key

    ip_config {
      ipv4 {
        address = each.value.ip
        gateway = "192.168.68.1"
      }
    }

    user_account {
      keys = [trimspace(file("~/.ssh/ansible_proxmox.pub"))]
    }
  }

  operating_system {
    template_file_id = each.value.template
    type             = "debian"
  }

  cpu { cores = each.value.cores }
  memory { dedicated = each.value.memory }

  disk {
    datastore_id = "local-lvm"
    size         = each.value.disk
  }

  network_interface {
    name   = "eth0"
    bridge = "vmbr0"
  }

  lifecycle {
    prevent_destroy = true
  }
}
