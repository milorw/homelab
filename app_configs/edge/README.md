## Mountpoints

The edge router LXC is mounted as follows:

```text
mp10: /tank/appdata/git_repo/app_configs/edge, mp=/opt/edge  
mp11: /tank/appdata, mp=/srv/appdata
```

`/opt/…` is the primary mountpoint for all config and Docker files.
`/srv/…` is the primary mountpoint for all LXC appdata.

## Generator

`generator.py` generates the Caddyfile and Corefile from a yaml config file, for easy maintenance of all domains and services passed through the edge router.

## Docker Compose Setup

The python generator service is built to an image so the Python dependencies and script + yaml are baked in, and then the compose file only has to create the container and run `python /app/generator.py` on (re)start.

The Caddy service needs to be built to include Cloudflare DNS options, allowing the use of the Cloudflare API for my domains.

The main compose file pulls the Caddy/Generator images from its tagged names in my `.env`.

Build commands:

1. `docker build -t service_name:date ./build_dir`

2. Update the `.env` image variables to their latest tags and reboot the containers

Note: each build directory contains a Dockerfile for the build process, and the generator directory contains the python script and ip config file.

This ensures that Python changes or script changes will not affect the edge router, unless the generator service is manually rebuilt.
