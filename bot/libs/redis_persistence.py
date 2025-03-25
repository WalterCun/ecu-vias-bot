#!/usr/bin/env python3
""" src/libs/redis_persistence.py """
from pprint import pprint

import redis.asyncio as aioredis
import pickle
from telegram.ext import BasePersistence


class RedisPersistence(BasePersistence):
    def __init__(self, redis_url='redis://localhost:6379/0'):
        super().__init__()
        self.redis = aioredis.StrictRedis.from_url(redis_url)

    # @print_result
    async def get_bot_data(self):
        raw_data = await self.redis.get('bot_data')
        return pickle.loads(raw_data) if raw_data else {}

    async def update_bot_data(self, data):
        await self.redis.set('bot_data', pickle.dumps(data))

    async def refresh_bot_data(self, data):
        await self.update_bot_data(data)

    # @print_result
    async def get_chat_data(self):
        raw_data = await self.redis.get('chat_data')
        data = pickle.loads(raw_data) if raw_data else {}
        print('get_chat_data:')
        pprint(data)  # Imprime el diccionario de manera más legible
        return pickle.loads(raw_data) if raw_data else {}

    async def update_chat_data(self, chat_id, chat_data):
        current_data = await self.get_chat_data()
        current_data[chat_id] = chat_data
        await self.redis.set('chat_data', pickle.dumps(current_data))

    async def refresh_chat_data(self, chat_id, chat_data):
        await self.update_chat_data(chat_id, chat_data)

    async def drop_chat_data(self, chat_id):
        current_data = await self.get_chat_data()
        if chat_id in current_data:
            del current_data[chat_id]
            await self.redis.set('chat_data', pickle.dumps(current_data))

    # @print_result
    async def get_user_data(self):
        raw_data = await self.redis.get('user_data')
        return pickle.loads(raw_data) if raw_data else {}

    async def update_user_data(self, user_id, user_data):
        current_data = await self.get_user_data()
        current_data[user_id] = user_data
        await self.redis.set('user_data', pickle.dumps(current_data))

    async def refresh_user_data(self, user_id, user_data):
        await self.update_user_data(user_id, user_data)

    # @print_result
    async def drop_user_data(self, user_id):
        current_data = await self.get_user_data()
        print('current_data', current_data)
        if user_id in current_data:
            del current_data[user_id]
            await self.redis.set('user_data', pickle.dumps(current_data))

    # @print_result
    # Implementación asíncrona de Callback Data
    async def get_callback_data(self):
        raw_data = await self.redis.get('callback_data')
        print('get_callback_data', raw_data)
        return pickle.loads(raw_data) if raw_data else {}

    async def update_callback_data(self, data):
        await self.redis.set('callback_data', pickle.dumps(data))

    # @print_result
    async def get_conversations(self, name):
        raw_data = await self.redis.get(f'conversations_{name}')
        print('get_conversations', raw_data)
        return pickle.loads(raw_data) if raw_data else {}

    async def update_conversation(self, name, key, new_state):
        conversations = await self.get_conversations(name)
        conversations[key] = new_state
        await self.redis.set(f'conversations_{name}', pickle.dumps(conversations))

    async def flush(self):
        await self.redis.flushdb()

    # @print_result
    # async def drop_conversation(self, name, key):
    #     conversations = await self.get_conversations(name)
    #     if key in conversations:
    #         del conversations[key]
    #         await self.redis.set(f'conversations_{name}', pickle.dumps(conversations))
    #
    # @print_result
    # async def refresh_conversations(self, name, conversations):
    #     await self.redis.set(f'conversations_{name}', pickle.dumps(conversations))
    #
    # @print_result
    # async def drop_callback_data(self):
    #     await self.redis.delete('callback_data')
    #
    # @print_result
    # async def refresh_callback_data(self, data):
    #     await self.update_callback_data(data)
