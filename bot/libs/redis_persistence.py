#!/usr/bin/env python3
"""Redis-backed JSON persistence for python-telegram-bot."""

from __future__ import annotations

import json
import logging
import pickle
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from telegram.ext import BasePersistence

try:
    import orjson  # type: ignore
except ImportError:  # pragma: no cover
    orjson = None


LOGGER = logging.getLogger(__name__)


class RedisJSONPersistence(BasePersistence):
    """Asynchronous JSON persistence using Redis hash structures.

    Data layout:
    - ``bot:data`` hash with field ``main``
    - ``bot:user_data`` hash with ``user_id`` fields
    - ``bot:chat_data`` hash with ``chat_id`` fields
    - ``bot:conversations:{handler_name}`` hash
    """

    BOT_DATA_KEY = "bot:data"
    BOT_DATA_FIELD = "main"
    USER_DATA_KEY = "bot:user_data"
    CHAT_DATA_KEY = "bot:chat_data"
    CALLBACK_DATA_KEY = "bot:callback_data"
    CONVERSATIONS_PREFIX = "bot:conversations:"

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        """Initialize persistence with an async Redis connection pool."""
        super().__init__()
        self._pool: ConnectionPool = ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
            max_connections=100,
        )
        self.redis: Redis = Redis(connection_pool=self._pool)

    def _serialize(self, data: dict) -> str:
        """Serialize a dict to JSON with UTF-8 characters preserved."""
        return self._serialize_value(data)

    def _deserialize(self, data: str) -> dict:
        """Deserialize JSON string data into a dict, filtering out null values."""
        value = self._deserialize_value(data)
        if isinstance(value, dict):
            return {k: v for k, v in value.items() if v is not None}
        return {}

    def _serialize_value(self, data: Any) -> str:
        """Serialize any JSON-compatible value, skipping non-serializable objects."""
        def _default_serializer(obj):
            # Skip service objects, schedulers, etc.
            LOGGER.debug("Skipping non-serializable object: %s", type(obj).__name__)
            return None

        if orjson is not None:
            return orjson.dumps(data, default=_default_serializer).decode("utf-8")
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=_default_serializer)

    def _deserialize_value(self, data: str) -> Any:
        """Deserialize JSON string data into a Python object."""
        try:
            if orjson is not None:
                return orjson.loads(data)
            return json.loads(data)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            LOGGER.error("Failed to deserialize JSON payload: %s", exc)
            return {}

    @staticmethod
    def _conversation_field(key: tuple[Any, ...]) -> str:
        """Serialize a conversation key tuple for Redis hash field storage."""
        if orjson is not None:
            return orjson.dumps(key).decode("utf-8")
        return json.dumps(key, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _parse_conversation_field(field: str) -> tuple[int, int] | None:
        """Deserialize a conversation field string back to ``(chat_id, user_id)``."""
        try:
            if orjson is not None:
                parsed = orjson.loads(field)
            else:
                parsed = json.loads(field)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            LOGGER.error("Invalid conversation key format (decode error): %s", exc)
            return None

        if not isinstance(parsed, list) or len(parsed) != 2:
            LOGGER.error("Invalid conversation key format (expected list of 2): %r", parsed)
            return None

        try:
            return int(parsed[0]), int(parsed[1])
        except (TypeError, ValueError) as exc:
            LOGGER.error("Invalid conversation key format (non-int items): %s", exc)
            return None

    async def get_user_data(self) -> dict[int, dict]:
        """Get all user data from Redis hash storage."""
        try:
            raw_map = await self.redis.hgetall(self.USER_DATA_KEY)
            return {
                int(user_id): self._deserialize(payload)
                for user_id, payload in raw_map.items()
            }
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while getting user data: %s", exc)
            return {}

    async def update_user_data(self, user_id: int, data: dict) -> None:
        """Persist user data for a single user in O(1)."""
        try:
            await self.redis.hset(self.USER_DATA_KEY, str(user_id), self._serialize(data))
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while updating user data: %s", exc)

    async def refresh_user_data(self, user_id: int, user_data: dict) -> None:
        """Refresh user data hook for BasePersistence."""
        await self.update_user_data(user_id, user_data)

    async def drop_user_data(self, user_id: int) -> None:
        """Remove user data for a single user."""
        try:
            await self.redis.hdel(self.USER_DATA_KEY, str(user_id))
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while dropping user data: %s", exc)

    async def get_chat_data(self) -> dict[int, dict]:
        """Get all chat data from Redis hash storage."""
        try:
            raw_map = await self.redis.hgetall(self.CHAT_DATA_KEY)
            return {
                int(chat_id): self._deserialize(payload)
                for chat_id, payload in raw_map.items()
            }
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while getting chat data: %s", exc)
            return {}

    async def update_chat_data(self, chat_id: int, data: dict) -> None:
        """Persist chat data for a single chat in O(1)."""
        try:
            await self.redis.hset(self.CHAT_DATA_KEY, str(chat_id), self._serialize(data))
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while updating chat data: %s", exc)

    async def refresh_chat_data(self, chat_id: int, chat_data: dict) -> None:
        """Refresh chat data hook for BasePersistence."""
        await self.update_chat_data(chat_id, chat_data)

    async def drop_chat_data(self, chat_id: int) -> None:
        """Remove chat data for a single chat."""
        try:
            await self.redis.hdel(self.CHAT_DATA_KEY, str(chat_id))
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while dropping chat data: %s", exc)

    async def get_user_data_by_id(self, user_id: int) -> dict:
        """Return user_data for a single user using O(1) HGET."""
        try:
            payload = await self.redis.hget(self.USER_DATA_KEY, str(user_id))
            if payload is None:
                return {}
            return self._deserialize(payload)
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while getting user data by id %s: %s", user_id, exc)
            return {}
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Unexpected error while getting user data by id %s: %s", user_id, exc)
            return {}

    async def get_chat_data_by_id(self, chat_id: int) -> dict:
        """Return chat_data for a single chat using O(1) HGET."""
        try:
            payload = await self.redis.hget(self.CHAT_DATA_KEY, str(chat_id))
            if payload is None:
                return {}
            return self._deserialize(payload)
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while getting chat data by id %s: %s", chat_id, exc)
            return {}
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Unexpected error while getting chat data by id %s: %s", chat_id, exc)
            return {}

    async def get_bot_data(self) -> dict:
        """Get bot-wide data."""
        try:
            payload = await self.redis.hget(self.BOT_DATA_KEY, self.BOT_DATA_FIELD)
            if payload is None:
                return {}
            return self._deserialize(payload)
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while getting bot data: %s", exc)
            return {}

    async def update_bot_data(self, data: dict) -> None:
        """Persist bot-wide data."""
        try:
            await self.redis.hset(
                self.BOT_DATA_KEY,
                self.BOT_DATA_FIELD,
                self._serialize(data),
            )
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while updating bot data: %s", exc)

    async def refresh_bot_data(self, data: dict) -> None:
        """Refresh bot data hook for BasePersistence."""
        await self.update_bot_data(data)

    async def get_callback_data(self) -> dict:
        """Get callback data payload."""
        try:
            payload = await self.redis.hget(self.CALLBACK_DATA_KEY, self.BOT_DATA_FIELD)
            if payload is None:
                return {}
            return self._deserialize(payload)
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while getting callback data: %s", exc)
            return {}

    async def update_callback_data(self, data: dict) -> None:
        """Persist callback data payload."""
        try:
            await self.redis.hset(
                self.CALLBACK_DATA_KEY,
                self.BOT_DATA_FIELD,
                self._serialize(data),
            )
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while updating callback data: %s", exc)

    async def drop_callback_data(self) -> None:
        """Drop callback data payload."""
        try:
            await self.redis.delete(self.CALLBACK_DATA_KEY)
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while dropping callback data: %s", exc)

    async def get_conversations(self, name: str) -> dict[tuple[int, int], object]:
        """Get all conversations for a handler."""
        redis_key = f"{self.CONVERSATIONS_PREFIX}{name}"
        try:
            raw_map = await self.redis.hgetall(redis_key)
            conversations: dict[tuple[int, int], object] = {}
            for field, value in raw_map.items():
                parsed_key = self._parse_conversation_field(field)
                if parsed_key is None:
                    continue
                conversations[parsed_key] = self._deserialize_value(value)
            return conversations
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while getting conversations: %s", exc)
            return {}

    async def update_conversation(self, name: str, key: tuple[int, int], new_state: object) -> None:
        """Persist a conversation state for a handler and key tuple."""
        redis_key = f"{self.CONVERSATIONS_PREFIX}{name}"
        field = self._conversation_field(key)
        try:
            if new_state is None:
                await self.redis.hdel(redis_key, field)
                return
            await self.redis.hset(redis_key, field, self._serialize_value(new_state))
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while updating conversation: %s", exc)


    async def drop_conversations(self, name: str) -> None:
        """Drop all conversations for a handler."""
        redis_key = f"{self.CONVERSATIONS_PREFIX}{name}"
        try:
            await self.redis.delete(redis_key)
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while dropping conversations: %s", exc)

    async def flush(self) -> None:
        """Flush Redis DB for this persistence instance."""
        try:
            await self.redis.flushdb()
        except RedisConnectionError as exc:
            LOGGER.error("Redis unavailable while flushing database: %s", exc)


class RedisPersistence(RedisJSONPersistence):
    """Backward-compatible alias for existing imports."""


async def migrate_from_pickle(redis_url: str) -> None:
    """Migrate legacy pickle-based persistence keys to JSON hash structures.

    This migration is idempotent and safe to run repeatedly.
    """
    legacy_redis = redis.from_url(redis_url, decode_responses=False)
    json_redis = redis.from_url(redis_url, decode_responses=True)

    def serialize_json(value: Any) -> str:
        if orjson is not None:
            return orjson.dumps(value).decode("utf-8")
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    try:
        legacy_bot_data = await legacy_redis.get("bot_data")
        if legacy_bot_data:
            try:
                bot_data = pickle.loads(legacy_bot_data)
                await json_redis.hset("bot:data", "main", serialize_json(bot_data))
                await legacy_redis.delete("bot_data")
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Failed to migrate key bot_data: %s", exc)

        legacy_user_data = await legacy_redis.get("user_data")
        if legacy_user_data:
            try:
                user_data = pickle.loads(legacy_user_data)
                if isinstance(user_data, dict):
                    for user_id, payload in user_data.items():
                        await json_redis.hset(
                            "bot:user_data",
                            str(int(user_id)),
                            serialize_json(payload),
                        )
                await legacy_redis.delete("user_data")
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Failed to migrate key user_data: %s", exc)

        legacy_chat_data = await legacy_redis.get("chat_data")
        if legacy_chat_data:
            try:
                chat_data = pickle.loads(legacy_chat_data)
                if isinstance(chat_data, dict):
                    for chat_id, payload in chat_data.items():
                        await json_redis.hset(
                            "bot:chat_data",
                            str(int(chat_id)),
                            serialize_json(payload),
                        )
                await legacy_redis.delete("chat_data")
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Failed to migrate key chat_data: %s", exc)

        async for raw_key in legacy_redis.scan_iter(match="conversations_*"):
            key_name = raw_key.decode("utf-8") if isinstance(raw_key, bytes) else str(raw_key)
            handler_name = key_name.split("conversations_", 1)[-1]
            target_key = f"bot:conversations:{handler_name}"

            try:
                raw_payload = await legacy_redis.get(raw_key)
                if not raw_payload:
                    continue

                conversations = pickle.loads(raw_payload)
                if isinstance(conversations, dict):
                    for conv_key, conv_state in conversations.items():
                        field = serialize_json(conv_key)
                        await json_redis.hset(target_key, field, serialize_json(conv_state))

                await legacy_redis.delete(raw_key)
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Failed to migrate key %s: %s", key_name, exc)
    except RedisConnectionError as exc:
        LOGGER.error("Redis unavailable during migration: %s", exc)
    finally:
        await legacy_redis.close()
        await json_redis.close()
