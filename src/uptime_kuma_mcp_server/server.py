"""Uptime Kuma MCP Server — Monitor-Inspection und -Verwaltung aus Claude.

Auth (identisch zu whisper-mcp / ntfy-mcp / n8n-mcp / hero-mcp):
  1. Statischer Bearer (MCP_API_KEY) → Claude Desktop / direkte Clients
  2. Bearer JWT → Authelia OIDC Introspection → Claude.ai
"""

import json
import logging
import os
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)

from . import client  # noqa: E402

server = Server(
    "uptime-kuma-mcp-server",
    instructions=(
        "MCP-Server für selbst gehostetes Uptime Kuma. Listet und manipuliert "
        "Monitore, holt Heartbeats und Uptime-Statistiken, verwaltet Status-Pages."
    ),
)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="uptime_list_monitors",
            description="Listet alle konfigurierten Monitore mit Type, URL, Status.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="uptime_get_monitor",
            description="Voll-Details zu einem Monitor inkl. Settings, Notifications, Tags.",
            inputSchema={
                "type": "object",
                "properties": {"monitor_id": {"type": "integer"}},
                "required": ["monitor_id"],
            },
        ),
        types.Tool(
            name="uptime_pause_monitor",
            description="Pausiert einen Monitor (kein Check mehr).",
            inputSchema={
                "type": "object",
                "properties": {"monitor_id": {"type": "integer"}},
                "required": ["monitor_id"],
            },
        ),
        types.Tool(
            name="uptime_resume_monitor",
            description="Reaktiviert einen pausierten Monitor.",
            inputSchema={
                "type": "object",
                "properties": {"monitor_id": {"type": "integer"}},
                "required": ["monitor_id"],
            },
        ),
        types.Tool(
            name="uptime_delete_monitor",
            description="Löscht einen Monitor permanent.",
            inputSchema={
                "type": "object",
                "properties": {"monitor_id": {"type": "integer"}},
                "required": ["monitor_id"],
            },
        ),
        types.Tool(
            name="uptime_add_monitor",
            description=(
                "Legt einen neuen Monitor an. type: http (HTTP-GET auf URL) / "
                "port (TCP-Port-Check) / ping (ICMP) / dns / keyword / docker. "
                "Je nach Type brauchst du url, hostname+port, oder hostname allein."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["http", "port", "ping", "dns", "keyword", "docker"],
                    },
                    "url": {
                        "type": "string",
                        "description": "Für type=http oder type=keyword",
                    },
                    "hostname": {
                        "type": "string",
                        "description": "Für type=port / ping / dns",
                    },
                    "port": {
                        "type": "integer",
                        "description": "Für type=port",
                    },
                    "interval": {
                        "type": "integer",
                        "default": 60,
                        "description": "Check-Intervall in Sekunden",
                    },
                    "max_retries": {
                        "type": "integer",
                        "default": 0,
                    },
                    "notification_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "IDs der Notification-Channels die alarmieren sollen",
                    },
                },
                "required": ["name", "type"],
            },
        ),
        types.Tool(
            name="uptime_get_heartbeats",
            description=(
                "Letzte Heartbeats. Mit monitor_id: letzte 24h dieses Monitors. "
                "Ohne: aktuelle Heartbeats aller Monitore."
            ),
            inputSchema={
                "type": "object",
                "properties": {"monitor_id": {"type": "integer"}},
            },
        ),
        types.Tool(
            name="uptime_get_uptime_stats",
            description="Aktuelle Uptime-Prozent-Werte je Monitor (24h / 30d).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="uptime_get_avg_response",
            description="Durchschnittliche Antwortzeit je Monitor.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="uptime_list_status_pages",
            description="Listet alle Status-Pages (Public Dashboards).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="uptime_get_status_page",
            description="Voll-Details einer Status-Page (Slug = URL-Pfad).",
            inputSchema={
                "type": "object",
                "properties": {"slug": {"type": "string"}},
                "required": ["slug"],
            },
        ),
        types.Tool(
            name="uptime_list_notifications",
            description="Listet alle konfigurierten Notification-Channels (Discord, Telegram, ntfy, …).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="uptime_list_tags",
            description="Listet alle Tags.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="uptime_list_maintenances",
            description="Listet konfigurierte Maintenance-Fenster.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="uptime_get_info",
            description="Server-Info (Version, Latency, Primary-Base-URL).",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    try:
        result = await _dispatch(name, arguments or {})
    except Exception as exc:
        result = {"error": str(exc), "tool": name}
    return [
        types.TextContent(
            type="text", text=json.dumps(result, ensure_ascii=False, indent=2, default=str)
        )
    ]


async def _dispatch(name: str, a: dict[str, Any]) -> Any:
    if name == "uptime_list_monitors":
        return await client.list_monitors()
    if name == "uptime_get_monitor":
        return await client.get_monitor(a["monitor_id"])
    if name == "uptime_pause_monitor":
        return await client.pause_monitor(a["monitor_id"])
    if name == "uptime_resume_monitor":
        return await client.resume_monitor(a["monitor_id"])
    if name == "uptime_delete_monitor":
        return await client.delete_monitor(a["monitor_id"])
    if name == "uptime_add_monitor":
        return await client.add_monitor(
            name=a["name"],
            type_=a["type"],
            url=a.get("url"),
            hostname=a.get("hostname"),
            port=a.get("port"),
            interval=a.get("interval", 60),
            max_retries=a.get("max_retries", 0),
            notification_ids=a.get("notification_ids"),
        )
    if name == "uptime_get_heartbeats":
        return await client.get_heartbeats(a.get("monitor_id"))
    if name == "uptime_get_uptime_stats":
        return await client.get_uptime()
    if name == "uptime_get_avg_response":
        return await client.get_avg_response()
    if name == "uptime_list_status_pages":
        return await client.list_status_pages()
    if name == "uptime_get_status_page":
        return await client.get_status_page(a["slug"])
    if name == "uptime_list_notifications":
        return await client.list_notifications()
    if name == "uptime_list_tags":
        return await client.list_tags()
    if name == "uptime_list_maintenances":
        return await client.list_maintenances()
    if name == "uptime_get_info":
        return await client.get_info()
    raise ValueError(f"Unbekanntes Tool: {name}")


def main() -> None:
    import asyncio

    if os.getenv("MCP_TRANSPORT", "stdio") == "sse":
        _run_sse()
    else:
        asyncio.run(mcp.server.stdio.run_server(server))


def _run_sse() -> None:
    import contextlib
    from collections.abc import AsyncIterator

    import httpx as _httpx
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Mount, Route

    mcp_api_key = os.getenv("MCP_API_KEY", "")
    oidc_introspection_url = os.getenv("OIDC_INTROSPECTION_URL", "")
    oidc_client_id = os.getenv("OIDC_CLIENT_ID", "")
    oidc_client_secret = os.getenv("OIDC_CLIENT_SECRET", "")

    async def _is_authorized(request: Request) -> tuple[bool, str | None]:
        if not mcp_api_key:
            return True, None
        auth = request.headers.get("Authorization", "")
        if not auth:
            return False, "no_header"
        if auth == f"Bearer {mcp_api_key}":
            return True, None
        if not auth.startswith("Bearer "):
            return False, "invalid_token"
        if oidc_introspection_url and oidc_client_id and oidc_client_secret:
            jwt_token = auth[7:]
            try:
                async with _httpx.AsyncClient() as http:
                    resp = await http.post(
                        oidc_introspection_url,
                        data={"token": jwt_token},
                        auth=(oidc_client_id, oidc_client_secret),
                        timeout=5.0,
                    )
                    data = resp.json()
                    if data.get("active", False):
                        return True, None
                    return False, "invalid_token"
            except Exception as e:
                logging.error("Introspection fehlgeschlagen: %s", e)
                return False, "invalid_token"
        return False, "invalid_token"

    def _unauthorized(reason: str | None) -> Response:
        if reason == "invalid_token":
            www = (
                'Bearer realm="uptime-kuma-mcp", error="invalid_token", '
                'error_description="The access token expired or is invalid"'
            )
            return Response(
                "Unauthorized",
                status_code=401,
                headers={"WWW-Authenticate": www},
            )
        return Response("Unauthorized", status_code=401)

    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        ok, reason = await _is_authorized(request)
        if not ok:
            return _unauthorized(reason)
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
        return Response()

    class _AlreadySent(Response):
        def __init__(self) -> None:
            super().__init__(content=b"", status_code=200)

        async def __call__(self, scope, receive, send):  # noqa: D401
            return

    session_manager = StreamableHTTPSessionManager(
        app=server,
        json_response=True,
    )

    async def handle_streamable_http(request: Request):
        ok, reason = await _is_authorized(request)
        if not ok:
            return _unauthorized(reason)
        await session_manager.handle_request(
            request.scope, request.receive, request._send
        )
        return _AlreadySent()

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logging.info("StreamableHTTPSessionManager started")
            yield
            logging.info("StreamableHTTPSessionManager stopping")

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_streamable_http, methods=["POST"]),
            Route("/mcp", endpoint=handle_streamable_http, methods=["POST"]),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
