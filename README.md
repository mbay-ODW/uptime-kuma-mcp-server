# uptime-kuma-mcp-server

> MCP-Server für selbst gehostetes [Uptime Kuma](https://github.com/louislam/uptime-kuma). Monitore verwalten + Stats abfragen aus Claude.

## Tools

| Tool | Zweck |
|---|---|
| `uptime_list_monitors` · `uptime_get_monitor` | Übersicht & Details |
| `uptime_add_monitor` · `uptime_delete_monitor` | CRUD (http/port/ping/dns/keyword/docker) |
| `uptime_pause_monitor` · `uptime_resume_monitor` | Lifecycle |
| `uptime_get_heartbeats` · `uptime_get_uptime_stats` · `uptime_get_avg_response` | Stats |
| `uptime_list_status_pages` · `uptime_get_status_page` | Public Dashboards |
| `uptime_list_notifications` · `uptime_list_tags` · `uptime_list_maintenances` | Verwaltung |
| `uptime_get_info` | Server-Info |

## Auth (identisch zu whisper-mcp / ntfy-mcp / n8n-mcp / hero-mcp)

1. **Statischer Bearer** (`MCP_API_KEY`) — Claude Desktop
2. **JWT via Authelia OIDC Introspection** — Claude.ai

Backend-Auth zu UK: API-Token (UK ≥1.23, Settings → API Keys) ODER User+Passwort.
