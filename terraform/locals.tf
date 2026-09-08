locals {
  # Shared network defaults for LXC resources.
  network = {
    gateway     = "192.168.68.1"
    bridge      = "vmbr0"
    dns_servers = ["192.168.68.1"]
    domain      = "local"
  }

  # Single place to see every static LXC IP allocation.
  lxc_ips = {
    samba       = "192.168.68.91/22"
    edge_router = "192.168.68.96/22"
    minecraft   = "192.168.68.98/22"
    docker_apps = "192.168.68.95/22"
  }

  # Host storage paths shared across LXCs, so containers mounting
  # the same dataset can't drift from each other.
  storage = {
    tank_shares           = "/tank/shares"
    tank_jellyfin         = "/tank/jellyfin"
    tank_shares_owen      = "/tank/shares/owen"
    tank_shares_common    = "/tank/shares/common"
    tank_shares_mrw       = "/tank/shares/mrw"
    tank_appdata          = "/tank/appdata"
    service_configs_samba = "/server_conf/service_configs/samba"

    # SSD-backed host directory, deliberately a plain host path, so it
    # survives an LXC rebuild while keeping SSD speed for world loading.
    ssd_minecraft = "/ssd/minecraft"
  }
}
