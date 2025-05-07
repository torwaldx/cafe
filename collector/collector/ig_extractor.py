import traceback
import os
import re

from shared.logging_config import setup_logger
from shared.models.models import Instagram_Account, Message

from .config import Settings
from .exceptions import MessageProcessingError
from .inst_api import InstAPI
from .llm import LanguageModel
from .message_service import MessageService
from .source_service import SourceService

logger = setup_logger()

HIKER_API_ACCESS_KEY = os.getenv('HIKER_API_ACCESS_KEY')
inst_api = InstAPI(HIKER_API_ACCESS_KEY)

llm = LanguageModel()
source_service = SourceService()
message_service = MessageService(llm)

async def add_account(username: str) -> Instagram_Account | None:
    try:
        user_id = inst_api.get_inst_user_id(username=username)
        acc = await source_service.add_inst_account(username, user_id)
        return acc
    except Exception as e:
        print(e)
        traceback.print_exc()
        return None


def extend_post(text: str) -> str: 
    pattern = r"\s(@[A-Za-z0-9._]+)[\s]*"
    links = list(dict.fromkeys(re.findall(pattern, text)))  # сохраняет порядок и удаляет дубликаты
    replacements = {link: inst_api.get_bio(link) for link in links[:2]}

    for link, replacement in replacements.items():
        text = text.replace(link, replacement)

    return text.strip()


async def process(account: Instagram_Account) -> list[Message]:
    new_posts = inst_api.get_new_posts(account, limit=Settings.LIMIT_INSTAGRAM_POSTS)

    messages = []
    if not new_posts:
        return []
    for post in new_posts:
        try:
            extended_text = extend_post(post["text"])
            msg = message_service.create_message(extended_text, account.source, post["external_id"])
            messages.append(msg)
        except MessageProcessingError as e:
            logger.info(f"Не удалось обработать сообщение: {e}")
            logger.info(f"{post['external_id']} - {post['text']}")
            continue

        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            traceback.print_exc()
            continue

    await source_service.instagram_account_update(account, new_posts[0]["timestamp"])

    return messages


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


async def receive_new_msgs():
    accounts = await source_service.get_active_inst_accounts()
    new_messages = []
    for account in accounts:
        try:
            messages = await process(account)
            new_messages.extend(messages)

        except Exception as e:
            logger.warning(f"Ошибка при обработке аккаунта {account.inst_username}: {e}")
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
        await receive_new_msgs()
    except Exception as e:
        logger.warning(f"Ошибка при сохранении новых сообщений: {e}")
        traceback.print_exc()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
