from bs4 import BeautifulSoup

from shared.logging_config import setup_logger

from .exceptions import DataExtractionError

logger = setup_logger()


class Bs4Parser:
    """Парсер HTML страницы Яндекс.Карт с использованием BeautifulSoup."""

    def __init__(self, html):
        try:
            self.soup = BeautifulSoup(html, "lxml")
        except Exception as e:
            logger.error(f"Произошла ошибка при разборе страницы: {str(e)}")

    def _get_text(self, class_name, tag_name="div"):
        tag = self.soup.find(tag_name, class_=class_name)
        return tag.text.strip() if tag else None

    def _get_attr_from_tag(self, tag, attr):
        return tag[attr] if tag and attr in tag.attrs else None

    def _sanitize_data(self, data: dict) -> dict:
        if "rating" in data and isinstance(data["rating"], str):
            data["rating"] = data["rating"].replace(",", ".")
        return data

    def get_est_dict(self) -> dict:
        try:
            results = self._get_est_data()
            return self._sanitize_data(results)
        except Exception as e:
            logger.error(f"Произошла ошибка при извлечении данных заведения: {str(e)}")
            raise DataExtractionError

    def _get_est_data(self) -> dict:
        """Извлечение информации из отдельной карточки заведения"""
        business_card_tag = self.soup.find("div", class_="business-card-view")

        coords = self._get_attr_from_tag(business_card_tag, "data-coordinates").split(",")
        if len(coords) == 2:
            longitude = coords[0]
            latitude = coords[1]
        else:
            longitude = None
            latitude = None

        return {
            "y_name": self._get_text("card-title-view__title-link", "a"),
            "y_address": self._get_text("business-contacts-view__address-link"),
            "yandex_id": self._get_attr_from_tag(business_card_tag, "data-id"),
            "rating": self._get_text("business-rating-badge-view__rating-text", "span"),
            "reviews_count": self._get_reviews_count(),
            "longitude": longitude,
            "latitude": latitude,
            "y_text": self._get_text("business-story-entry-view__description"),
        }

    def get_images(self) -> list:
        image_tags = self.soup.find_all("img", class_="img-with-alt")
        return [img["src"] for img in image_tags if "src" in img.attrs]

    def get_categories(self) -> list:
        """Получение типов заведения, приведены к нижнему регистру"""
        categories_tags = self.soup.find_all(
            "a", class_="business-categories-view__category _outline _clickable"
        )
        return [categories_tag.text.strip().lower() for categories_tag in categories_tags]

    def _get_reviews_count(self) -> int:
        reviews_counter = self.soup.select_one(
            "div.tabs-select-view__title._name_reviews div.tabs-select-view__counter"
        )
        if reviews_counter:
            return int(reviews_counter.text.strip())
        return None
