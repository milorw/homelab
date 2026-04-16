The edge router LXC is mounted as follows:

```text
mp10: /tank/appdata/git_repo/app_configs/edge, mp=/opt/edge  
mp11: /tank/appdata/edge, mp=/opt/edge/data
```

An empty `/edge` folder lives in the Git repo as a mount point, and the working LXC scratch folder gets mounted there.

`generator.py` generates the Caddyfile and Corefile from a list of url → ip maps, for easy maintenance. 

`compose.yaml` is the main compose file, and it regenerates the Caddyfile/Corefile whenever docker is (re)started.

Example ip_config.yaml layout:

```yaml
# config.yml  
tailscale_ip: 100.0.0.0
  
# Define TLS profiles once (which env var to use)  
tls_profiles:  
 cloudflare_api_1:  
   env_var: CF_API_TOKEN_CF1
 cloudflare_api_2:  
   env_var: CF_API_TOKEN_CF2
  
# Canonical services list (shared across domains)  
services:  
 homebox:  
   upstream: "0.0.0.0:3100"  
   encode: ["gzip", "zstd"]  
 sure:  
   upstream: "0.0.0.0:3000"  
   encode: ["gzip", "zstd"]  
 proxmox:  
   upstream: "https://0.0.0.0:8006"  
   proxmox: true   # turn on special reverse_proxy transport+headers  
  
 jellyfin:  
   upstream: "http://0.0.0.0:8096"  
   encode: ["gzip", "zstd"]  
  
 ha:  
   upstream: "0.0.0.0:8123"  
   encode: ["gzip", "zstd"]  
  
# Domains decide which services they expose  
domains:  
 - name: "domain1.com"  
   tls_profile: "cloudflare_api_1"  
   services: ["homebox", "sure", "proxmox", "jellyfin", "ha"]  
  
 - name: "domain2.com"  
   tls_profile: "cloudflare_api_2"  
   services: ["homebox", "sure", "jellyfin", "ha"]
```


build note:
docker build -t edge-generator:2026-03-13 ./generator


