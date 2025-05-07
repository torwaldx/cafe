from datetime import datetime, timezone

from sqlalchemy import text

from shared.logging_config import setup_logger
from shared.models.models import Category, Establishment, Message, Y_Image

from .bs4_parser import Bs4Parser
from .comparsion_helper import are_equivalent
from .config import Settings
from .exceptions import AddDescriptionError, AddEstablishmentError, EstablishmentProcessingError
from .llm import LanguageModel
from .selenium_manager import SeleniumManager

logger = setup_logger()

class EstHandler:
    def __init__(
        self,
        selenium_manager: SeleniumManager,
        lang_model: LanguageModel
    ):
        self.selenium_manager = selenium_manager
        self.lang_model = lang_model


    async def _save_images(self,establishment, image_urls) -> bool:
        
        try:
            images = [Y_Image(
                establishment=establishment.id,
                link=link
            ) for link in image_urls]

            await Y_Image.objects.bulk_create(images)

        except (Exception) as e:
            logger.warning(f"Ошибка при сохранении изображений: {e}")
            return False
        
        return True
    
    async def mark_message_processed(self, msg: Message):
        msg.attempt_count += 1
        msg.processed_at = datetime.now(timezone.utc)
        await msg.update(_columns=["processed_at", "attempt_count", "establishment"])
    
    async def save_message_with_establishment(self, msg: Message, est: Establishment):
        msg.establishment = est
        await self.mark_message_processed(msg)

    async def save_establishment(self, est_data: dict, message: Message) -> Establishment:
        """Добавляет новое заведение и привязывает сообщение.
        Если Заведение с таким же yandex_id уже существует, привязывает его к сообщению
        """
        try:
            yandex_id = est_data.pop('yandex_id')

            establishment, created = await Establishment.objects.get_or_create(
                yandex_id=yandex_id,
                _defaults = est_data
            )

            if not created:
                message.establishment = establishment
                raise AddEstablishmentError(
                    "заведение уже существует, сообщение привязано "
                )
            
            await self.save_message_with_establishment(message, establishment)

            logger.info("заведение успешно добавлено")
            return establishment
 
        except (Exception) as e:
            raise AddEstablishmentError(str(e))
        
    async def _add_categories(self, establishment, categories):
        try:
            db = Establishment.ormar_config.database
            async with db.transaction():
                
                for i, category in enumerate(categories[:10]):
                    category_model, _ = await Category.objects.get_or_create(
                        name=category
                    )
                    await category_model.establishments.add(
                        establishment,
                        sort_order=i
                    )
                logger.info("Категории успешно назначены")
                return True
        except (Exception) as e:
            logger.warning(f"Ошибка при добавлении категорий: {e}")
            return False
        

    async def add_description(self, est: Establishment, msg: Message) -> None:
        try:
            description = self.lang_model.get_description(
                msg.text,
                est.y_text
            )
            est.gen_text = description
            await est.update(_columns=['gen_text', 'updated'])
        except Exception as e:
            logger.warning(f"Ошибка при добавлении описания: {e}")
            raise AddDescriptionError(f"Заведение: {est.y_name} (id: {est.id})")
        
    async def get_new_messages(self):
        return await Message.objects.filter(
            (Message.establishment.id.isnull(True))
            & Message.estimated_address.isnull(False)
            & Message.estimated_name.isnull(False)
            & (Message.attempt_count < Settings.MAX_ATTEMPTS)
            & (
                # Либо еще не обрабатывалось
                # либо не раньше чем через число дней по числу попыток
                Message.processed_at.isnull(True) |
                (Message.processed_at <= text("DATE_SUB(NOW(), INTERVAL attempt_count DAY)"))
            )
        ).limit(Settings.MAX_MESSAGES).all()

    async def process_messages(self) -> None:

        messages = await self.get_new_messages()

        logger.info(f"Получено сообщений: {len(messages)}")
        succeeded = 0

        for message in messages:
            result = await self.process(message)
            if result:
                succeeded += 1
        logger.info(f"Успешно обработано сообщений: {succeeded}/{len(messages)}")
    
    async def process(self, message: Message) -> bool:
        try:    
            est_data = self.get_est_data(message)
            establishment = await self.save_establishment(est_data, message)

            await self.add_description(establishment, message)

            categories = self.parser.get_categories()
            if categories:
                await self._add_categories(establishment, categories)

            image_urls = self.parser.get_images()
            if image_urls:
                await self._save_images(establishment, image_urls)

            logger.info(f"Обработка сообщения завершена: {message.id}, {message.estimated_name}")
            logger.info(str(est_data))
            # logger.info(str(image_urls))
            logger.info(str(categories))
            logger.info(establishment.model_dump_json(indent=4))

            return True        
        except Exception as e:
            await self.handle_failure(message)
            logger.error(f"Ошибка при обработке сообщения {message.id}")
            logger.error(str(e), exc_info=True)
            return False

    def get_est_data(self,message: Message)->dict:
        query = f"Кафе {message.estimated_name}, Москва, {message.estimated_address}"
        logger.info(f"Обработка по запросу: {query}")
        html = self.selenium_manager.get_establishment_html(query, message)
        self.parser = Bs4Parser(html)
        est_data = self.parser.get_est_dict()
        if not self.is_valid_establishment(est_data, message):
            err = f"Название не соответствует: \n{query} - {est_data['y_name']}"
            raise EstablishmentProcessingError(err)
        return est_data

    def is_valid_establishment(self, est_data: dict, msg: Message) -> bool:
        return are_equivalent(est_data['y_name'], msg.estimated_name)
        
    async def handle_failure(self, message: Message) -> None:
        await self.mark_message_processed(message)
        logger.warning(f"Failed to process message {message.id}, attempts: {message.attempt_count}")


