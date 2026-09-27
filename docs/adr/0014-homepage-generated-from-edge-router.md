## Generate the Homepage Dashboard from the Edge Router's Config

### Context

A dashboard of every service needs a list of services and their URLs, and `edge_router.yml` (`edge_domains` / `edge_services`) already is that list. Maintaining a second hand-written list in the dashboard's config would drift from the reverse proxy the first time a service was added or removed.

### Decision

Deploy [homepage](https://gethomepage.dev) on the docker_apps LXC, and render its `services.yaml` from the edge router's host vars. Only services present in every `edge_domains` entry are listed (so every link works on both domains), and `homepage_link_domain` picks which domain the links use. Display details (name, icon, description, group), widgets, and container status mappings are optional per-service overrides in `group_vars/docker_apps.yml`.

### Consequences

Pros

- Adding a service to the edge router adds it to the dashboard
- The dashboard can't list a service the proxy doesn't serve

Cons

- `docker-apps.yml` now depends on the edge router's inventory vars
- A service only on one domain won't appear
- Widgets with API keys render secrets into `services.yaml`, so that file is `0640` and its task is `no_log`
