variable "pve_node" {
  type    = string
  default = "proxmox"
}

variable "proxmox_ssh_public_key" {
  type        = string
  description = "Public key installed into the container's root account"
}
