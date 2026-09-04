resource "proxmox_virtual_environment_container" "samba" {
  node_name     = var.pve_node
  vm_id         = 100
  unprivileged  = true
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
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst"
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
  mount_point {
    volume = local.storage.service_configs_samba
    path   = "/etc/samba"
  }

  # lxc.idmap - one block per line, uid and gid separately
  idmap {
    type         = "uid"
    container_id = 0
    host_id      = 100000
    size         = 1000
  }

  idmap {
    type         = "gid"
    container_id = 0
    host_id      = 100000
    size         = 1000
  }

  idmap {
    type         = "uid"
    container_id = 1000
    host_id      = 1000
    size         = 101
  }

  idmap {
    type         = "gid"
    container_id = 1000
    host_id      = 1000
    size         = 101
  }

  idmap {
    type         = "uid"
    container_id = 1101
    host_id      = 101101
    size         = 64435
  }

  idmap {
    type         = "gid"
    container_id = 1101
    host_id      = 101101
    size         = 64435
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [operating_system[0].template_file_id]
  }
}
