resource "proxmox_virtual_environment_container" "minecraft" {
  node_name     = var.pve_node
  vm_id         = 110
  unprivileged  = true
  start_on_boot = true
  started       = true

  tags = ["terraform", "lxc", "role_minecraft"]

  cpu {
    cores = 4
  }

  memory {
    dedicated = 3072
    swap      = 2048
  }

  features {
    keyctl  = false
    nesting = true
  }

  initialization {
    hostname = "minecraft.local"

    ip_config {
      ipv4 {
        address = "192.168.68.98/22"
        gateway = "192.168.68.1"
      }
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
    bridge      = "vmbr0"
    firewall    = true
    mac_address = "BC:24:11:2F:EE:D7"
  }

  mount_point {
    volume = "local-lvm:vm-110-disk-1"
    path   = "/srv/minecraft"
    size   = "32G"
    backup = true
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [operating_system[0].template_file_id]
  }
}
