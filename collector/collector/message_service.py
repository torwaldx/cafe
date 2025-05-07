from shared.models.models import Message

from .exceptions import MessageProcessingError
from .llm import LanguageModel


class MessageService:
    def __init__(self, llm: LanguageModel):
        self.llm = llm

    def create_message(self, text, source, external_id):
        if not text:
            raise MessageProcessingError("В сообщении нет текста")
        msg = Message(source=source, external_id=external_id, text=text)

        return msg

    def set_llm_info(self, msg: Message):
        est_info = self.llm.get_info(msg.text)

        if not est_info.get("name") or not est_info.get("address"):
            raise MessageProcessingError("Не удалось разобрать заведение:\n" + str(est_info))

        msg.estimated_name = est_info["name"]
        msg.estimated_address = est_info["address"]
        msg.estimated_category = est_info["category"]

    async def save_messages(self, messages):
        await Message.objects.bulk_create(messages)
