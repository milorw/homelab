resource "proxmox_virtual_environment_container" "test" {
  node_name = var.pve_node
  vm_id     = 999

  initialization {
    hostname = "tf-test"

    ip_config {
      ipv4 {
        address = "192.168.68.99/24"
        gateway = "192.168.68.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst"
    type             = "debian"
  }

  cpu { cores = 1 }
  memory { dedicated = 512 }

  disk {
    datastore_id = "local-lvm"
    size         = 4
  }

  network_interface {
    name   = "eth0"
    bridge = "vmbr0"
  }
}
