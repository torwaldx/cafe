from shared.logging_config import setup_logger
from shared.models.db import database

from .est_handler import EstHandler
from .llm import LanguageModel
from .selenium_manager import SeleniumManager

logger = setup_logger()


async def main():
    await database.connect()

    try:
        selenium_mgr = SeleniumManager()
        lang_model = LanguageModel()
        parser = EstHandler(selenium_mgr, lang_model)
        await parser.process_messages()
    finally:
        await database.disconnect()
        selenium_mgr.quit()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
