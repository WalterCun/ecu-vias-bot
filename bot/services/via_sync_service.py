"""Service for syncing API road data to the Tortoise ORM database."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pytz
from tortoise import Tortoise

from bot.db.models import (
    Provincia,
    Canton,
    Centro,
    EstadoActual,
    CategoriaVia,
    Via,
    ViaAlterna,
)

LOGGER = logging.getLogger(__name__)
ECUADOR_TZ = pytz.timezone("America/Guayaquil")

TORTOISE_CONFIG = {
    "connections": {
        "default": "sqlite://ecuavias.db"
    },
    "apps": {
        "models": {
            "models": ["bot.db.models"],
            "default_connection": "default",
        }
    },
}


class ViaSyncService:
    """Synchronize API road data into the local SQLite database via Tortoise ORM."""

    def __init__(self, db_url: str | None = None) -> None:
        if db_url:
            TORTOISE_CONFIG["connections"]["default"] = db_url
        self._initialized = False

    async def init_db(self) -> None:
        """Initialize Tortoise ORM connection and generate schemas."""
        if self._initialized:
            return
        await Tortoise.init(config=TORTOISE_CONFIG)
        await Tortoise.generate_schemas(safe=True)
        self._initialized = True
        LOGGER.info("Tortoise ORM initialized with %s", TORTOISE_CONFIG["connections"]["default"])

    async def close_db(self) -> None:
        """Close Tortoise ORM connections."""
        if self._initialized:
            await Tortoise.close_connections()
            self._initialized = False
            LOGGER.info("Tortoise ORM connections closed")

    async def sync_vias(self, api_data: list[dict[str, Any]]) -> dict[str, int]:
        """
        Sync API road data into the database.

        Args:
            api_data: List of road records from ECU 911 API.

        Returns:
            Dict with counts: {"created": N, "updated": N, "unchanged": N, "errors": N}
        """
        if not self._initialized:
            LOGGER.error("DB not initialized, skipping sync")
            return {"created": 0, "updated": 0, "unchanged": 0, "errors": 0}

        # Ensure Tortoise connection is alive
        try:
            conn = Tortoise.get_connection("default")
            await conn.execute_query("SELECT 1")
        except Exception:
            LOGGER.warning("DB connection lost, reconnecting...")
            try:
                await Tortoise.close_connections()
                await Tortoise.init(config=TORTOISE_CONFIG)
                await Tortoise.generate_schemas(safe=True)
                LOGGER.info("DB reconnected successfully")
            except Exception as exc:
                LOGGER.error("Failed to reconnect DB: %s", exc)
                return {"created": 0, "updated": 0, "unchanged": 0, "errors": len(api_data)}

        LOGGER.info("Starting sync with %d records from API", len(api_data))
        stats = {"created": 0, "updated": 0, "unchanged": 0, "errors": 0}
        now = datetime.now(ECUADOR_TZ)

        for row in api_data:
            try:
                await self._sync_single_via(row, now, stats)
            except Exception as exc:
                stats["errors"] += 1
                LOGGER.error("Error syncing via record: %s — %s", exc, row.get("descripcion", "?"))

        LOGGER.info(
            "Sync complete: %d created, %d updated, %d unchanged, %d errors",
            stats["created"], stats["updated"], stats["unchanged"], stats["errors"],
        )
        return stats

    async def _sync_single_via(self, row: dict[str, Any], now: datetime, stats: dict[str, int]) -> None:
        """Sync a single API row to the database."""
        # Extract nested data from API response
        # API structure: { Provincia, Canton, Centro, EstadoActual, GroupDetail, ... }
        provincia_data = row.get("Provincia", {})
        canton_data = row.get("Canton", {})
        centro_data = row.get("Centro", {})
        estado_data = row.get("EstadoActual", {})
        group_detail = row.get("GroupDetail", {})  # NOT "CategoriaVia"

        provincia_name = provincia_data.get("descripcion", "").strip()
        via_desc = row.get("descripcion", "").strip()
        estado_nombre = estado_data.get("nombre", "").strip()

        if not provincia_name or not via_desc:
            return

        # Upsert related entities
        provincia, _ = await Provincia.get_or_create(
            descripcion=provincia_name,
            defaults={"codigo": provincia_data.get("codigo", "")},
        )

        canton_desc = canton_data.get("descripcion", "").strip()
        canton = None
        if canton_desc:
            canton, _ = await Canton.get_or_create(
                descripcion=canton_desc,
                provincia=provincia,
            )

        # API uses "nombre" not "descripcion" for Centro
        centro_nombre = centro_data.get("nombre", "").strip()
        centro = None
        if centro_nombre:
            centro, _ = await Centro.get_or_create(
                nombre=centro_nombre,
                provincia=provincia,
            )

        estado_actual = None
        if estado_nombre:
            estado_actual, _ = await EstadoActual.get_or_create(nombre=estado_nombre)

        # API uses "GroupDetail" with "nombre" field, not "CategoriaVia"
        cat_nombre = group_detail.get("nombre", "").strip()
        categoria = None
        if cat_nombre:
            categoria, _ = await CategoriaVia.get_or_create(nombre=cat_nombre)

        # Check if via already exists
        existing = await Via.filter(descripcion=via_desc, provincia=provincia).first()

        observaciones = row.get("observaciones", "")
        estado_char = row.get("estado", "A")

        if existing:
            # Check if anything changed
            changed = (
                existing.observaciones != observaciones
                or existing.estado != estado_char
                or (estado_actual and existing.estado_actual_id != estado_actual.id)
            )

            if changed:
                existing.observaciones = observaciones
                existing.estado = estado_char
                existing.modified = now
                if estado_actual:
                    existing.estado_actual = estado_actual
                await existing.save()
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1
        else:
            # Create new record
            via = await Via.create(
                descripcion=via_desc,
                codigo=row.get("id"),
                observaciones=observaciones,
                estado=estado_char,
                created=now,
                modified=now,
                provincia=provincia,
                canton=canton,
                centro=centro,
                estado_actual=estado_actual,
                categoria=categoria,
            )
            stats["created"] += 1

            # Handle alternate routes from DetalleViaAlterna
            alternas = row.get("DetalleViaAlterna", [])
            if isinstance(alternas, list):
                for alterna in alternas:
                    alterna_via = alterna.get("Via", {})
                    alterna_desc = alterna_via.get("descripcion", "").strip()
                    if alterna_desc:
                        # Via inside DetalleViaAlterna has provincia_id, not nested Provincia
                        # Use the same province as the parent via
                        alt_via, _ = await Via.get_or_create(
                            descripcion=alterna_desc,
                            provincia=provincia,
                            defaults={"estado": "A", "created": now},
                        )
                        await ViaAlterna.create(via=via, via_alterna=alt_via, created=now)

    async def get_vias_by_province(self, province: str) -> list[dict[str, Any]]:
        """Get all vias for a province from the database."""
        if not self._initialized:
            LOGGER.warning("DB not initialized for get_vias_by_province")
            return []

        # Ensure connection alive
        try:
            conn = Tortoise.get_connection("default")
            await conn.execute_query("SELECT 1")
        except Exception:
            LOGGER.warning("DB connection lost in get_vias_by_province, reconnecting...")
            try:
                await Tortoise.close_connections()
                await Tortoise.init(config=TORTOISE_CONFIG)
                await Tortoise.generate_schemas(safe=True)
            except Exception as exc:
                LOGGER.error("Failed to reconnect: %s", exc)
                return []

        vias = await Via.filter(
            provincia__descripcion__iexact=province
        ).prefetch_related("provincia", "estado_actual", "categoria", "canton").all()

        return [
            {
                "id": str(v.id),
                "descripcion": v.descripcion,
                "estado": v.estado,
                "observaciones": v.observaciones,
                "provincia": v.provincia.descripcion if v.provincia else None,
                "estado_actual": v.estado_actual.nombre if v.estado_actual else None,
                "categoria": v.categoria.nombre if v.categoria else None,
                "canton": v.canton.descripcion if v.canton else None,
            }
            for v in vias
        ]

    async def get_vias_from_api(self, province: str, via_service: Any) -> list[dict[str, Any]]:
        """Fallback: get vias directly from API via ViaService (no DB needed)."""
        LOGGER.info("Fallback: querying API directly for province: %s", province)
        try:
            vias_by_province = await via_service.get_latest_vias()
            rows = vias_by_province.get(province.lower(), [])
            LOGGER.info("API returned %d rows for province %s", len(rows), province)
            return [
                {
                    "descripcion": row.get("descripcion", "?"),
                    "estado": row.get("estado", "A"),
                    "estado_actual": row.get("EstadoActual", {}).get("nombre", "?"),
                    "observaciones": row.get("observaciones", ""),
                    "provincia": row.get("Provincia", {}).get("descripcion", province),
                    "canton": row.get("Canton", {}).get("descripcion", ""),
                    "categoria": row.get("GroupDetail", {}).get("nombre", ""),
                }
                for row in rows
            ]
        except Exception as exc:
            LOGGER.error("Error fetching vias from API: %s", exc)
            return []

    async def get_all_provinces(self) -> list[str]:
        """Get list of all provinces in the database."""
        if not self._initialized:
            return []
        rows = await Provincia.all().values_list("descripcion", flat=True)
        return sorted(set(rows))
