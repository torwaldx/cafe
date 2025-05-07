import os

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class LanguageModel:
    def __init__(self):
        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

        self.llm = ChatOpenAI(
            openai_api_base=api_base,
            model_name="gpt-4o-mini",
            temperature=0.0,
        )

        self.get_info_chain = self._get_info_extraction_chain()

    def _get_description_generation_chain(self):
        system_message = """Ты - умный ИИ помощник. Ты помогаешь генерировать описание заведения.
Описание должно быть основано на пользовательском тексте, состоять из двух-трех предложений в неофициальном стиле.
Описание не должно содержать негативные оценки, слова и отзывы.
Описание может содержать сведения о кухне (особенностях блюд), если их можно извлечь из предоставленного текста.
В описание не требуется включать название и адрес заведения.
Твой ответ должен содержать только описание заведения, без дополнительных пояснений.
"""

        prompt = ChatPromptTemplate(
            [
                ("system", system_message),
                ("human", "{user_request}"),
            ]
        )

        chain = prompt | self.llm

        return chain

    def _get_info_extraction_chain(self):
        system_message = """Ты - умный ИИ помощник.
Ты помогаешь из текста сообщения извлечь название, категорию и адрес заведения общественного питания.
Заведения не относящиеся к категории общественного питания должны быть проигнорированы.
Название и адрес заведения должны явным образом содержаться в тексте.
Если в сообщении есть несколько категорий, то они должны быть разделены запятыми. Первой в списке категорий должна быть категория, наиболее подходящая по смыслу сообщения.
Адрес должен состоять из названия улицы (обязательно) и номера дома или строения (по возможности).
Данные адреса должны быть извлечены только для тех заведений, которые находятся в Москве (Moscow, msk, Мск), поэтому, если в тексте прослеживается принадлежность адреса к другому грроду, этот адрес должен быть проигнорирован.

Формат ответа: JSON-объект с ключом "items", содержащий словарь с полями "name" (название заведения), "category" (категория) и "address" (адрес).
Если по какой-либо причине не удается однозначно из текста определить название, категорию или адрес заведения, то в качестве ответа верни пустую строку.
Ответ должен быть строго JSON-объектом без пояснений и дополнительного текста.

Примеры ответов:

Сообщение пользователя: "Новый ресторан «Аврора» на Цветном бульваре — это три этажа, которые в свое время наделали много шума. Внешне спокойный интерьер, ближе к сдержанной классике, чем к «Сахалину» — но это на мой, скромный взгляд
Avrora — место, куда стоит прийти без ожиданий. Внятная, но не идеальная кухня, иногда похожая на самоповтор от AVA Team
Приемлемые цены, грамотное обслуживание. Не сказать, что здесь вас ждет откровение, но стабильное качество в красивых декорациях — вполне.
🏴 Цветной бульвар, 2 
📞 8 (495) 846-93-66
"
Ответ:
{{
    "items": {{
        "name": "Аврора",
        "category": "ресторан",
        "address": "Цветной бульвар, 2"
    }}
}}


Сообщение пользователя: " На обед в нашем ресторане сегодня выгодное предложение — ловите скидки на покупки до 50%

Крутите колесо (https://plus.yandex.ru/x5?utm_source=plus&utm_medium=smm_paid&utm_campaign=MSCAMP-632_wheel_march&utm_content=posev_tg&utm_term=vkusonomika&erid=2VtzquveYNL) и забирайте до 100 000 баллов Плюса, скидки до 50% в «Перекрёстке», до 25% в «Пятёрочке» и другие подарки. Акция действует один день для подписчиков"
"
Ответ:
{{
    "items": {{
        "name": "",
        "category": "ресторан",
        "address": ""
    }}
}}

Сообщение пользователя: "Fitz Джин открылись!

Ресторан-бар с европейской кухней и авторскими коктейлями! Оттянись у стойки!

◻️ Мясницкая, 14/2 c1
◻️ Работают с 18:00
◻️ Подробности (https://fitzginbar.ru/)

#Открытие #Москва #ЦАО
"
Ответ:
{{
    "items": {{
        "name": "Fitz Джин",
        "category": "бар, ресторан",
        "address": "Мясницкая, 14/2 c1"
    }}
}}
    """

        prompt = ChatPromptTemplate(
            [
                ("system", system_message),
                ("human", "{user_request}"),
            ]
        )

        parser = JsonOutputParser()

        chain = prompt | self.llm | parser

        return chain

    def _is_valid_types(self, response):
        if type(response) is not dict:
            return False
        if response.get("items") is None:
            return False
        if response["items"].get("name") is None or response["items"].get("address") is None:
            return False
        if type(response["items"]["name"]) is not str or type(response["items"]["address"]) is not str:
            return False
        if len(response["items"]["name"]) == 0 or len(response["items"]["address"]) == 0:
            return False

        return True

    def _is_info_in_text(self, response, text):
        return True
        words_list = response["items"]["address"].split() + response["items"]["name"].split()
        return all(words_list[i] in text for i in range(len(words_list)))

    def _is_valid_info(self, response, text):
        if not self._is_valid_types(response):
            return False
        if not self._is_info_in_text(response, text):
            return False
        return True

    def get_info(self, text: str):
        response = self.get_info_chain.invoke({"user_request": text})
        if self._is_valid_info(response, text):
            return response["items"]
        return {"name": None, "address": None}

    def get_description(self, *args) -> str:
        request = ".\n".join(str(arg) for arg in args if arg is not None)
        chain = self._get_description_generation_chain()
        return chain.invoke({"user_request": request}).content
