"""Domain service for retrieving and caching latest road status data."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any


LOGGER = logging.getLogger(__name__)


class ViaService:
    """Provide cached access to latest vias grouped by province."""

    def __init__(self, http_client: Any, cache_ttl: int = 60) -> None:
        """Initialize service with an async-compatible HTTP client and TTL."""
        self.http_client = http_client
        self.cache_ttl = cache_ttl
        self._cache_by_province: dict[str, list[dict[str, Any]]] = {}
        self._cache_timestamp_by_province: dict[str, float] = {}
        self._last_refresh_at: float = 0.0
        self._lock = asyncio.Lock()

    def _is_cache_fresh(self, now: float) -> bool:
        """Return whether the full province cache is still within the TTL window."""
        if not self._cache_by_province:
            return False
        return (now - self._last_refresh_at) < self.cache_ttl

    @staticmethod
    def _extract_rows(payload: Any) -> list[dict[str, Any]]:
        """Extract the list of row dictionaries from multiple response formats."""
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]

        if isinstance(payload, dict):
            data = payload.get("data", [])
            if isinstance(data, list):
                return [row for row in data if isinstance(row, dict)]

        return []

    @staticmethod
    def _extract_province(row: dict[str, Any]) -> str | None:
        """Extract and normalize province name from an API row."""
        provincia = row.get("Provincia")
        if isinstance(provincia, dict):
            descripcion = provincia.get("descripcion")
            if isinstance(descripcion, str) and descripcion.strip():
                return descripcion.strip().lower()

        province = row.get("province")
        if isinstance(province, str) and province.strip():
            return province.strip().lower()

        return None

    async def _fetch_payload(self) -> Any:
        """Fetch payload from configured HTTP client using common method names."""
        if hasattr(self.http_client, "get_latest_vias"):
            result = self.http_client.get_latest_vias()
        elif hasattr(self.http_client, "get_states_vias"):
            result = self.http_client.get_states_vias()
        else:
            raise AttributeError("http_client must implement get_latest_vias or get_states_vias")

        if asyncio.iscoroutine(result):
            return await result
        return result

    async def get_latest_vias(self) -> dict[str, list[dict[str, Any]]]:
        """Return latest vias grouped by province, using in-memory TTL cache."""
        now = time.monotonic()
        if self._is_cache_fresh(now):
            LOGGER.debug("Returning cached vias (%d provinces)", len(self._cache_by_province))
            return {province: rows[:] for province, rows in self._cache_by_province.items()}

        async with self._lock:
            now = time.monotonic()
            if self._is_cache_fresh(now):
                return {province: rows[:] for province, rows in self._cache_by_province.items()}

            LOGGER.info("Fetching fresh vias from API...")
            try:
                payload = await self._fetch_payload()
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Failed to fetch latest vias: %s", exc)
                return {province: rows[:] for province, rows in self._cache_by_province.items()}

            rows = self._extract_rows(payload)
            LOGGER.info("Received %d rows from API", len(rows))
            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

            for row in rows:
                province = self._extract_province(row)
                if province is None:
                    continue
                grouped[province].append(row)

            new_cache = {province: province_rows for province, province_rows in grouped.items()}
            refreshed_at = time.monotonic()
            self._cache_by_province = new_cache
            self._cache_timestamp_by_province = {
                province: refreshed_at for province in new_cache
            }
            self._last_refresh_at = refreshed_at

            return {province: province_rows[:] for province, province_rows in new_cache.items()}
