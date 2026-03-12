#!/usr/bin/env python3
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.resolve()
CONFIG_PATH = ROOT / "ip_config.yml"
OUT_CADDY = "/srv/appdata/edge/caddy_data/Caddyfile"
OUT_CORE = "/srv/appdata/edge/coredns_data/Corefile"


def require(d, key, ctx=""):
    if key not in d:
        raise KeyError(f"Missing required key '{key}'{(' in ' + ctx) if ctx else ''}")
    return d[key]

def caddy_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')

def main():
    cfg = yaml.safe_load(CONFIG_PATH.read_text())
    tailscale_ip = require(cfg, "tailscale_ip", "root")

    tls_profiles = require(cfg, "tls_profiles", "root")
    services = require(cfg, "services", "root")
    domains = require(cfg, "domains", "root")

    # --- Build Caddyfile ---
    caddy_lines = []
    caddy_lines.append("# GENERATED FILE - DO NOT EDIT")
    caddy_lines.append("# Source: config.yml")
    caddy_lines.append("")

    # TLS snippets
    for prof_name, prof in tls_profiles.items():
        env_var = require(prof, "env_var", f"tls_profiles.{prof_name}")
        caddy_lines.append(f"(cf_{prof_name}) {{")
        caddy_lines.append("  tls {")
        caddy_lines.append(f"    dns cloudflare {{env.{env_var}}}")
        caddy_lines.append("  }")
        caddy_lines.append("}")
        caddy_lines.append("")

    # Service snippets (so upstream lives once)
    for svc_name, svc in services.items():
        upstream = require(svc, "upstream", f"services.{svc_name}")
        encode = svc.get("encode", [])
        proxmox = bool(svc.get("proxmox", False))

        caddy_lines.append(f"({svc_name}_common) {{")
        caddy_lines.append(f"  bind {tailscale_ip}")
        if encode:
            caddy_lines.append("  encode " + " ".join(encode))
        if proxmox:
            # Proxmox-specific reverse proxy settings
            caddy_lines.append(f"  reverse_proxy {upstream} {{")
            caddy_lines.append("    transport http {")
            caddy_lines.append("      tls_insecure_skip_verify")
            caddy_lines.append("    }")
            caddy_lines.append("    header_up Host {host}")
            caddy_lines.append("    header_up X-Forwarded-Proto https")
            caddy_lines.append("    header_up X-Forwarded-Host {host}")
            caddy_lines.append("    header_up X-Forwarded-Port 443")
            caddy_lines.append("  }")
        else:
            caddy_lines.append(f"  reverse_proxy {upstream}")
        caddy_lines.append("}")
        caddy_lines.append("")

    # Sites
    for d in domains:
        domain_name = require(d, "name", "domains[]")
        tls_profile = require(d, "tls_profile", f"domains[{domain_name}]")
        svc_list = require(d, "services", f"domains[{domain_name}]")
        if tls_profile not in tls_profiles:
            raise KeyError(f"domains[{domain_name}].tls_profile '{tls_profile}' not found in tls_profiles")

        for svc_name in svc_list:
            if svc_name not in services:
                raise KeyError(f"domains[{domain_name}] references unknown service '{svc_name}'")
            host = f"{svc_name}.{domain_name}"
            caddy_lines.append(f"{host} {{")
            caddy_lines.append(f"  import cf_{tls_profile}")
            caddy_lines.append(f"  import {svc_name}_common")
            caddy_lines.append("}")
            caddy_lines.append("")

    with open(OUT_CADDY, 'w') as f:
        f.write("\n".join(caddy_lines))

    # --- Build Corefile ---
    core_lines = []
    core_lines.append("# GENERATED FILE - DO NOT EDIT")
    core_lines.append("# Source: config.yml")
    core_lines.append("")
    core_lines.append(".:53 {")
    core_lines.append("  errors")
    core_lines.append("  log")
    core_lines.append("  health")
    core_lines.append("  ready")
    core_lines.append("")

    # Use explicit host mappings to preserve flexibility and avoid collisions.
    # The hosts plugin is simplest and fast.
    core_lines.append("  hosts {")
    for d in domains:
        domain_name = require(d, "name", "domains[]")
        svc_list = require(d, "services", f"domains[{domain_name}]")
        names = [f"{svc}.{domain_name}" for svc in svc_list]
        if names:
            core_lines.append(f"    {tailscale_ip} " + " ".join(names))
    core_lines.append("    fallthrough")
    core_lines.append("  }")
    core_lines.append("")
    core_lines.append("  forward . 1.1.1.1 8.8.8.8")
    core_lines.append("  cache 30")
    core_lines.append("}")
    core_lines.append("")

    with open(OUT_CORE, 'w') as f:
        f.write("\n".join(core_lines))

    print(f"Wrote: {OUT_CADDY}")
    print(f"Wrote: {OUT_CORE}")

if __name__ == "__main__":
    main()
