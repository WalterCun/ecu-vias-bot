"""Policy for detecting province-level vias changes."""

from __future__ import annotations

from typing import Any


class NotificationPolicy:
    """Compare snapshots of vias and return grouped changes by province."""

    @staticmethod
    def _incident_key(incident: dict[str, Any]) -> str:
        for key in ("id", "Id", "codigo", "code", "name", "title", "descripcion"):
            value = incident.get(key)
            if value is not None:
                text = str(value).strip()
                if text:
                    return text
        return str(sorted(incident.items()))

    @staticmethod
    def _incident_status(incident: dict[str, Any]) -> str:
        for key in ("status", "estado", "Estado", "estado_actual", "EstadoActual"):
            value = incident.get(key)
            if value is not None:
                return str(value)
        return ""

    def compare(
        self,
        old_vias: dict[str, list[dict[str, Any]]],
        new_vias: dict[str, list[dict[str, Any]]],
    ) -> dict[str, dict[str, list[dict[str, Any]]]]:
        """Return per-province new/removed/updated incidents."""
        provinces = set(old_vias) | set(new_vias)
        result: dict[str, dict[str, list[dict[str, Any]]]] = {}

        for province in provinces:
            old_items = [row for row in old_vias.get(province, []) if isinstance(row, dict)]
            new_items = [row for row in new_vias.get(province, []) if isinstance(row, dict)]

            old_map = {self._incident_key(item): item for item in old_items}
            new_map = {self._incident_key(item): item for item in new_items}

            new_keys = set(new_map) - set(old_map)
            removed_keys = set(old_map) - set(new_map)
            shared_keys = set(old_map) & set(new_map)

            updated: list[dict[str, Any]] = []
            for key in shared_keys:
                if self._incident_status(old_map[key]) != self._incident_status(new_map[key]):
                    updated.append(new_map[key])

            result[province] = {
                "new": [new_map[key] for key in new_keys],
                "removed": [old_map[key] for key in removed_keys],
                "updated": updated,
            }

        return result
