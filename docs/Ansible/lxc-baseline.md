## LXC Baseline

[`ansible/playbooks/lxc-baseline.yml`](../../ansible/playbooks/lxc-baseline.yml) applies settings that should be the same on every LXC, whatever it's for. It targets `proxmox_all_lxc`, the group the Proxmox inventory plugin creates for every container, so a new LXC is covered without any extra tagging. Its vars are in `ansible/inventory/group_vars/proxmox_all_lxc.yml`.

```bash
cd ansible
ansible-playbook playbooks/lxc-baseline.yml
```

Anything specific to one service belongs in that LXC's own playbook, not here.

### Root SSH policy

Every LXC already allowed root login by key only - but only because that's OpenSSH's default on Debian. A different base image, or a package dropping its own file into `sshd_config.d`, could change that silently. The playbook sets it explicitly in `/etc/ssh/sshd_config.d/10-root-login.conf`, from `lxc_permit_root_login`:

```
PermitRootLogin prohibit-password
```

**Don't set it to `no`** without first giving Ansible its own sudo-capable account. `ansible_user` is `root`, so `no` locks Ansible out of every LXC at once.

### Not locking itself out

A broken sshd config followed by a reload would leave a container unreachable, so the play is careful about the order:

1. Write the drop-in.
2. Test the whole config with `sshd -t` (a drop-in can't be validated on its own).
3. If sshd rejects it, remove the drop-in again and fail the play, including sshd's error. The reload is a handler, and a failed play never runs handlers, so a rejected config is never loaded.
4. Otherwise reload sshd (`ssh.service` on Debian - `lxc_sshd_service`), read the effective setting back with `sshd -T`, and check it matches. If it doesn't, something later in the include order is overriding it.

`sshd -T` reports `prohibit-password` under its older name, `without-password`, so the check accepts either.
