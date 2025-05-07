import os

from telethon import TelegramClient
from telethon.tl.types import Channel

from shared.logging_config import setup_logger
from shared.models.models import Tg_Channel

logger = setup_logger()

class TgChannelMonitor:
    def __init__(self, max_messages=99):
        self.client = TelegramClient(
            api_id=os.getenv("TG_API_ID"),
            api_hash=os.getenv("TG_API_HASH"),
            session='./tg_sessions/' + os.getenv("TG_SESSION"),
            system_version="5.15.10-vxCUSTOM",
        )
        self.max_messages = max_messages

    async def __aenter__(self):
        """Асинхронный вход в контекстный менеджер"""
        await self.client.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Асинхронный выход из контекстного менеджера"""
        await self.client.disconnect()

    async def get_channel_entity(self, ch_ident):
        """Получает сущность канала по ссылке"""
        try:
            entity = await self.client.get_entity(ch_ident)

            if not isinstance(entity, Channel):
                raise ValueError("Указанный чат не является каналом")
            return entity
        except Exception as e:
            logger.warning(f"Ошибка при получении канала: {e}")
            return None

    async def get_unread_messages(self, channel: Tg_Channel):
        """Получает непрочитанные сообщения из канала"""
        ch_ident = channel.tg_link if channel.tg_link else channel.tg_name
        print(ch_ident)

        entity = await self.get_channel_entity(ch_ident)
        if not entity:
            return []

        messages = await self.client.get_messages(
            entity,
            min_id=channel.last_message_id,
            limit=self.max_messages,
        )

        return messages
