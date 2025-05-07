
from datetime import datetime, timedelta, timezone

from shared.logging_config import setup_logger
from shared.models.models import Message

from .config import Settings

logger = setup_logger()

async def delete_old_messages(period: int = 30) -> int:
    threshold_date = datetime.now(timezone.utc) - timedelta(days=period)

    deleted_count = await Message.objects.filter(
        (
            Message.estimated_name.isnull(True)
            | Message.estimated_address.isnull(True)
        )
        & (Message.created_at < threshold_date)
    ).delete()

    return deleted_count


async def main():
    
    async with Message.ormar_config.database:
        period = Settings.UNNEEDED_MESSAGE_RETENTION_DAYS
        logger.info(f"Удаление нераспознанных сообщений старше, чем {period} дней")
        try:
            num_deleted = await delete_old_messages(period)
            logger.info(f"Удалено {num_deleted} сообщений")
        except Exception as e:
            logger.error(f"Ошибка удаления сообщений: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())