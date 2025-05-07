
import random
from datetime import datetime
from platform import system
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from shared.logging_config import setup_logger
from shared.models.models import Message

from .comparsion_helper import get_simple_score, get_tr_score
from .config import Settings
from .exceptions import HtmlNotLoadedError

logger = setup_logger()


class SeleniumManager:
    def __init__(self, restart_interval=Settings.RESTART_INTERVAL):
        self.restart_interval = restart_interval  # Количество запросов до перезапуска
        self.timeout = 10
        self.request_count = 0
        self.driver = self._create_driver()

    def _create_driver(self) -> webdriver.Chrome:
        """Создание и настройка драйвера с оптимизированными параметрами."""
        options = webdriver.ChromeOptions()

        # Отключаем загрузку изображений
        # options.add_experimental_option(
        #     "prefs", {"profile.managed_default_content_settings.images": 2}
        # )

        # Отключаем кэш
        # options.add_argument("--disable-application-cache")
        # options.add_argument("--disk-cache-size=0")
        # options.add_argument("--disable-cache")

        # options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1120,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")

        if system() == "Linux":
            options.add_argument("--blink-settings=imagesEnabled=false")
            options.add_argument("--headless=new")
            service = Service("/usr/bin/chromedriver")
            return webdriver.Chrome(service=service, options=options)
        return webdriver.Chrome(options=options)

    def _random_sleep(self, min_seconds=2, max_seconds=6) -> None:
        """Приостанавливает выполнение на случайное время в пределах заданных интервалов."""
        sleep(random.uniform(min_seconds, max_seconds))

    def _load_info_block(self, search_str, message: Message):
        self._search(search_str)

        if self._is_single_result():
            logger.info("Single result")
            return self._get_business_block()

        self._safe_scroll()
        blocks = self.driver.find_elements(By.CLASS_NAME, "search-snippet-view")
        relevant_link = self._get_relevant(blocks, message)

        if not relevant_link:
            logger.warning("Проверка результатов не дала результатов")
            return None

        relevant_link.click()

        if self._is_single_result():
            logger.info("Single result from many")
            return self._get_business_block()

        return None

    def get_establishment_html(self, search_str: str, message: Message):
        """Загружает страницу и возвращает HTML."""
        # Перезапускаем драйвер при необходимости

        self.request_count += 1
        if self.request_count >= self.restart_interval:
            self._restart_driver()
        try:
            info_block = self._load_info_block(search_str, message)
        
            if not info_block:
                raise HtmlNotLoadedError()

            return info_block.get_attribute("innerHTML")

        except Exception as e:
            logger.error(f"Ошибка при загрузке данных по запросу {search_str}")
            logger.error(f"Ошибка: {str(e)}", exc_info=True)
            self.save_screenshot()
            raise

    def _get_business_block(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-chunk="business"]')

        if len(elements) > 1:
            logger.warning("Блоков больше одного")
            return None
        if not elements:
            logger.warning("Блок не найден")
            return None

        el = elements[0]
        container = self.driver.execute_script(
            "return arguments[0].closest('.scroll__container');", el
        )
        self._safe_scroll(container)
        return el

    def _is_single_result(self) -> bool:
        logger.debug("URL check:\n" + self.driver.current_url)
        return "https://yandex.ru/maps/org/" in self.driver.current_url

    def _safe_scroll(self, block_element=None, offset_y=150):
        if block_element is None:
            block_element = self.driver
        try:
            self._random_sleep(5, 9)
            locator = (By.CLASS_NAME, "scroll__scrollbar-thumb")
            slider = WebDriverWait(block_element, 2).until(
                EC.visibility_of_element_located(locator)
            )

            ActionChains(self.driver).click_and_hold(slider).move_by_offset(
                0, offset_y
            ).release().perform()
            logger.info("Результаты поиска прокручены")
            self._random_sleep(4, 8)
        except TimeoutException:
            logger.warning("прокрутка пропущена")

    def _search(self, search_str: str) -> None:
        self._random_sleep()
        self.driver.get("https://yandex.ru/maps")
        wait = WebDriverWait(self.driver, self.timeout)
        # Ожидание загрузки поля ввода строки поиска
        self._random_sleep()
        logger.info("Вводим данные")
        input_locator = (
            By.XPATH,
            '//div[@class="search-form-view__input"]//input[@class="input__control _bold"]',
        )
        search_input = wait.until(EC.element_to_be_clickable(input_locator))
        search_input.send_keys(search_str)
        logger.info("введена строка поиска")
        self._random_sleep(1, 3)

        # Клик по кнопке поиска
        search_button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "small-search-form-view__button"))
        )
        search_button.click()
        logger.info("отправлен запрос поиска")
        self._random_sleep(5, 7)

    def _get_relevant(self, blocks, message):
        max_score = 0
        relevant_block = None
        logger.info(f"Найдено блоков: {len(blocks)}")

        if len(blocks) == 1:
            try:
                title = blocks[0].find_element(By.CLASS_NAME, "search-business-snippet-view__title")
                return title
            except Exception:
                return None

        for block in blocks or []:
            try:
                title = block.find_element(By.CLASS_NAME, "search-business-snippet-view__title")
                address = block.find_element(By.CLASS_NAME, "search-business-snippet-view__address")
                score = self._get_score(title.text, address.text, message)

                if score > max_score:
                    max_score = score
                    relevant_block = title
            except Exception:
                continue

        return relevant_block

    def _get_score(self, name, address, message: Message):
        name_score = get_tr_score(name, message.estimated_name)
        address_score = get_simple_score(address, message.estimated_address)
        return name_score + address_score

    def save_screenshot(self):
        print('saving')
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshots/screenshot_{timestamp}.png"
        print(filename)
        self.driver.save_screenshot(filename)

    def _restart_driver(self):
        """Перезапускает драйвер и сбрасывает счетчик."""
        logger.info("[INFO] Перезапуск драйвера...")
        self.driver.quit()
        self._random_sleep(15, 25)
        self.driver = self._create_driver()
        self.request_count = 0

    def quit(self):
        """Закрывает драйвер."""
        if self.driver:
            self.driver.quit()
