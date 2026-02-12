"""Utilities to build notification messages for vias updates."""

from __future__ import annotations

from typing import Any


class MessageBuilder:
    """Build human-readable notification messages for province changes."""

    TELEGRAM_MAX_LENGTH = 4096
    _TRUNCATE_AT = 4000
    _SECTION_LIMIT = 12

    @classmethod
    def _incident_title(cls, incident: dict[str, Any]) -> str:
        """Extract a readable title from an incident payload."""
        for key in ("name", "title", "descripcion", "description", "id"):
            value = incident.get(key)
            if value is not None:
                text = str(value).strip()
                if text:
                    return text
        return "Incidente sin título"

    @classmethod
    def _render_section(cls, label: str, items: list[dict[str, Any]]) -> list[str]:
        """Render one change section with bounded item output."""
        lines = [f"{label} ({len(items)}):"]

        if not items:
            lines.append("• Sin cambios")
            return lines

        for incident in items[: cls._SECTION_LIMIT]:
            lines.append(f"• {cls._incident_title(incident)}")

        remaining = len(items) - cls._SECTION_LIMIT
        if remaining > 0:
            lines.append(f"• … y {remaining} más")

        return lines

    @classmethod
    def _truncate(cls, message: str) -> str:
        """Trim long messages while keeping Telegram limits and readable formatting."""
        suffix = "... (truncated)"

        if len(message) <= cls._TRUNCATE_AT:
            return message

        allowed = min(cls._TRUNCATE_AT, cls.TELEGRAM_MAX_LENGTH) - len(suffix)
        truncated = message[: max(0, allowed)].rstrip() + suffix

        if len(truncated) > cls.TELEGRAM_MAX_LENGTH:
            truncated = truncated[: cls.TELEGRAM_MAX_LENGTH - len(suffix)].rstrip() + suffix

        return truncated

    @classmethod
    def build_notification(cls, province: str, changes: dict) -> str:
        """Build a notification summary for one province.

        Args:
            province: Province name.
            changes: Mapping with `new`, `removed`, and `updated` incident lists.

        Returns:
            A formatted plain-text message ready to send.
        """
        province_name = str(province).strip() or "provincia desconocida"

        new_items = changes.get("new", []) if isinstance(changes, dict) else []
        removed_items = changes.get("removed", []) if isinstance(changes, dict) else []
        updated_items = changes.get("updated", []) if isinstance(changes, dict) else []

        new_items = [item for item in new_items if isinstance(item, dict)]
        removed_items = [item for item in removed_items if isinstance(item, dict)]
        updated_items = [item for item in updated_items if isinstance(item, dict)]

        lines: list[str] = [f"🚦 Actualización de vías: {province_name}", ""]
        lines.extend(cls._render_section("🆕 Nuevas incidencias", new_items))
        lines.append("")
        lines.extend(cls._render_section("✅ Incidencias removidas", removed_items))
        lines.append("")
        lines.extend(cls._render_section("🔄 Incidencias actualizadas", updated_items))

        return cls._truncate("\n".join(lines))
