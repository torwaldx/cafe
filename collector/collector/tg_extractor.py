import traceback

from shared.logging_config import setup_logger
from shared.models.models import Message, Tg_Channel

from .config import Settings
from .exceptions import MessageProcessingError
from .llm import LanguageModel
from .message_service import MessageService
from .source_service import SourceService
from .tg_manager import TgChannelMonitor

logger = setup_logger()

llm = LanguageModel()
message_service = MessageService(llm)
source_service = SourceService()


async def process(channel: Tg_Channel, tg: TgChannelMonitor) -> list[Message]:
    tg_messages = await tg.get_unread_messages(channel)

    if len(tg_messages) < 1:
        return []

    last_message_id = max(tg_messages, key=lambda msg: msg.id).id

    new_messages = []

    for tg_msg in tg_messages:
        try:
            msg_entity = message_service.create_message(tg_msg.text, channel.source, str(tg_msg.id))

        except MessageProcessingError as e:
            logger.info(f"Не удалось обработать сообщение: {e}")
            logger.info(f"{tg_msg.id} - {tg_msg.text}")
            continue

        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            traceback.print_exc()
            continue

        new_messages.append(msg_entity)

    await source_service.tg_channel_update(channel, last_message_id)

    return new_messages


def bulk_set_llm_info(messages: list[Message]) -> list[Message]:
    succeed_count = 0
    for msg in messages:
        try:
            message_service.set_llm_info(msg)
            succeed_count += 1
        except MessageProcessingError as e:
            logger.info(f"Не удалось обработать сообщение: {e}")
            continue
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            traceback.print_exc()
            continue
    logger.info(f"Распознано через LLM {succeed_count} сообщений")
    return messages


async def receive_new_messages():
    channels = await source_service.get_active_tg_channels()
    new_messages = []
    async with TgChannelMonitor(max_messages=Settings.LIMIT_TG_MESSAGES) as tg:
        for channel in channels:
            try:
                channel_msgs = await process(channel, tg)
                new_messages.extend(channel_msgs)
            except Exception as e:
                logger.warning(f"Ошибка при обработке канала {channel.name}: {e}")
                traceback.print_exc()
                continue

    logger.info(f"Получено новых сообщений: {len(new_messages)}")
    if len(new_messages) < 1:
        return
    bulk_set_llm_info(new_messages)
    await message_service.save_messages(new_messages)
    logger.info(f"Cохранено {len(new_messages)} сообщений")


async def main():
    db = Message.ormar_config.database
    await db.connect()
    try:
        await receive_new_messages()
    except Exception as e:
        logger.warning(f"Ошибка при сохранении новых сообщений: {e}")
        traceback.print_exc()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
