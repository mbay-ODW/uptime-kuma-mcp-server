"""Uptime Kuma Socket.IO client wrapper — synchronous Lib in async-Welt.

`uptime-kuma-api` ist blockierend; wir wrappen jeden Call in einen
ThreadPoolExecutor und cachen den UptimeKumaApi-Connection per Lock.
"""

import asyncio
import logging
import os
import threading
from typing import Any

from dotenv import load_dotenv
from uptime_kuma_api import MonitorType, UptimeKumaApi

load_dotenv()

UPTIME_KUMA_URL = os.getenv("UPTIME_KUMA_URL", "").rstrip("/")
UPTIME_KUMA_TOKEN = os.getenv("UPTIME_KUMA_TOKEN", "")
UPTIME_KUMA_USERNAME = os.getenv("UPTIME_KUMA_USERNAME", "")
UPTIME_KUMA_PASSWORD = os.getenv("UPTIME_KUMA_PASSWORD", "")

_log = logging.getLogger(__name__)

# Single shared connection (Socket.IO ist persistent) + lock damit nicht zwei
# Threads gleichzeitig drauf zugreifen
_api: UptimeKumaApi | None = None
_api_lock = threading.Lock()


def _check_config() -> None:
    if not UPTIME_KUMA_URL:
        raise RuntimeError("UPTIME_KUMA_URL muss gesetzt sein.")
    if not UPTIME_KUMA_TOKEN and not (UPTIME_KUMA_USERNAME and UPTIME_KUMA_PASSWORD):
        raise RuntimeError(
            "Entweder UPTIME_KUMA_TOKEN ODER UPTIME_KUMA_USERNAME + UPTIME_KUMA_PASSWORD setzen."
        )


def _connect() -> UptimeKumaApi:
    """Connect + login. Hot-cached, idempotent."""
    global _api
    with _api_lock:
        if _api is not None:
            # Heartbeat-Check: war die Verbindung weg?
            try:
                _api.info()
                return _api
            except Exception:
                _log.warning("Stale connection, reconnect")
                try:
                    _api.disconnect()
                except Exception:
                    pass
                _api = None

        _check_config()
        api = UptimeKumaApi(UPTIME_KUMA_URL)
        if UPTIME_KUMA_TOKEN:
            api.login_by_token(UPTIME_KUMA_TOKEN)
        else:
            api.login(UPTIME_KUMA_USERNAME, UPTIME_KUMA_PASSWORD)
        _api = api
        return _api


async def _run_sync(fn, *args, **kwargs) -> Any:
    """Blockierende uptime-kuma-api-Calls in Thread auslagern."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# ── Monitore ────────────────────────────────────────────────────────────


async def list_monitors() -> list[dict[str, Any]]:
    def _go():
        return _connect().get_monitors()
    return await _run_sync(_go)


async def get_monitor(monitor_id: int) -> dict[str, Any]:
    def _go():
        return _connect().get_monitor(monitor_id)
    return await _run_sync(_go)


async def pause_monitor(monitor_id: int) -> dict[str, Any]:
    def _go():
        return _connect().pause_monitor(monitor_id)
    return await _run_sync(_go)


async def resume_monitor(monitor_id: int) -> dict[str, Any]:
    def _go():
        return _connect().resume_monitor(monitor_id)
    return await _run_sync(_go)


async def delete_monitor(monitor_id: int) -> dict[str, Any]:
    def _go():
        return _connect().delete_monitor(monitor_id)
    return await _run_sync(_go)


async def add_monitor(
    name: str,
    type_: str,
    url: str | None = None,
    hostname: str | None = None,
    port: int | None = None,
    interval: int = 60,
    max_retries: int = 0,
    notification_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Neuen Monitor anlegen. type_: 'http' | 'port' | 'ping' | 'dns' | 'keyword' | …"""
    type_map = {
        "http": MonitorType.HTTP,
        "port": MonitorType.PORT,
        "ping": MonitorType.PING,
        "dns": MonitorType.DNS,
        "keyword": MonitorType.KEYWORD,
        "docker": MonitorType.DOCKER,
    }
    mtype = type_map.get(type_.lower())
    if not mtype:
        raise ValueError(f"Unbekannter Monitor-Typ: {type_}")

    args: dict[str, Any] = {
        "type": mtype,
        "name": name,
        "interval": interval,
        "maxretries": max_retries,
    }
    if url:
        args["url"] = url
    if hostname:
        args["hostname"] = hostname
    if port:
        args["port"] = port
    if notification_ids:
        args["notificationIDList"] = {str(n): True for n in notification_ids}

    def _go():
        return _connect().add_monitor(**args)
    return await _run_sync(_go)


# ── Heartbeats / Uptime ─────────────────────────────────────────────────


async def get_heartbeats(monitor_id: int | None = None) -> Any:
    def _go():
        api = _connect()
        if monitor_id is not None:
            return api.get_monitor_beats(monitor_id, 24)  # letzte 24h
        return api.get_heartbeats()
    return await _run_sync(_go)


async def get_uptime() -> dict[str, Any]:
    def _go():
        return _connect().uptime
    return await _run_sync(_go)


async def get_avg_response() -> dict[str, Any]:
    def _go():
        return _connect().avg_ping
    return await _run_sync(_go)


# ── Status-Pages ────────────────────────────────────────────────────────


async def list_status_pages() -> list[dict[str, Any]]:
    def _go():
        return _connect().get_status_pages()
    return await _run_sync(_go)


async def get_status_page(slug: str) -> dict[str, Any]:
    def _go():
        return _connect().get_status_page(slug)
    return await _run_sync(_go)


# ── Notifications / Tags / Maintenance ──────────────────────────────────


async def list_notifications() -> list[dict[str, Any]]:
    def _go():
        return _connect().get_notifications()
    return await _run_sync(_go)


async def list_tags() -> list[dict[str, Any]]:
    def _go():
        return _connect().get_tags()
    return await _run_sync(_go)


async def list_maintenances() -> list[dict[str, Any]]:
    def _go():
        return _connect().get_maintenances()
    return await _run_sync(_go)


async def get_info() -> dict[str, Any]:
    def _go():
        return _connect().info()
    return await _run_sync(_go)
