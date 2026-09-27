## Serve Error Pages from the Edge Router

### Context

When a backend was down, Caddy returned a bare 502. Worse, a powered-off backend host drops SYNs rather than refusing them, so the browser hung on the OS TCP timeout (minutes) before showing anything.

### Decision

Every HTTP service in the Caddyfile gets:

- a short `dial_timeout` (`edge_dial_timeout`), so an unreachable host fails fast
- `handle_errors 502 503 504` serving `unreachable.html` when Caddy gets no response at all
- `handle_response` on a 502/503/504 from the backend itself, serving `starting.html`

Both pages are rendered from `templates/edge_router/error.html.j2` onto the edge router's own disk, fully inline, so they're servable exactly when the app host isn't. They retry the original URL a few times, then hand off to the homepage. Both are sent with `Cache-Control: no-store`. `transport_http` became a list so the dial timeout and per-service transport options can share one `transport http` block.

### Consequences

Pros

- Users get a clear page that retries by itself instead of a raw 502 or a hang
- No dependency on the backend host to show the error

Cons

- "Stopped" and "still booting" can't be told apart from the edge (a published container port refuses the connection either way), so `unreachable.html` covers both
- More Caddyfile template logic to maintain
