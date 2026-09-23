# utils/scraper.py
import os
import time
from pathlib import Path
import requests
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.logger import logger
from src.utils.errors import ErrorHandler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from src.config.setting import default_chrome_settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
COOKIES_PATH = DATA_DIR / "cookies.json"

class CookieManager:
    """Управление авторизацией и сессионными куками VK"""
    def __init__(self, driver, cookies_file: Path = COOKIES_PATH):
        self.driver = driver
        self.cookies_file = cookies_file

    def has_cookies(self) -> bool:
        """Проверяет наличие файла с куками"""
        return self.cookies_file.exists() and self.cookies_file.stat().st_size > 0

    def save_cookies(self):
        """Интерактивный вход и сохранение куки в JSON"""
        logger.warning("Файл с куки не найден или пуст.")
        logger.info("Пожалуйста, авторизуйтесь в открывшемся окне браузера...")

        input("[ACTION] После успешной авторизации в VK нажмите ENTER в этой консоли...")

        os.makedirs(self.cookies_file.parent, exist_ok=True)
        cookies = self.driver.get_cookies()

        with open(self.cookies_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)

        logger.success(f"Куки успешно сохранены в: {self.cookies_file}")

    def is_authenticated(self, timeout=10):
        """Проверяет, что VK показывает элементы авторизованного пользователя."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "#l_pr, [data-testid='header_avatar'], .TopNavBtn, #myprofile_wrap"
                ))
            )
            return True
        except Exception:
            return False

    def load_cookies(self):
        """Подгрузка куки из файла в текущую сессию браузера"""
        if not self.has_cookies():
            logger.error("Нельзя загрузить куки: файл не существует!")
            return False

        logger.info("Загружаем сохраненные куки...")

        if "vk.ru" not in self.driver.current_url:
            self.driver.get("https://vk.ru")

        with open(self.cookies_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        loaded_count = 0
        skipped_count = 0
        for cookie in cookies:
            if "expiry" in cookie:
                cookie["expiry"] = int(cookie["expiry"])
                if cookie["expiry"] <= int(time.time()):
                    skipped_count += 1
                    continue
            try:
                self.driver.add_cookie(cookie)
                loaded_count += 1
            except Exception as error:
                skipped_count += 1
                logger.warning(
                    f"Не удалось добавить cookie {cookie.get('name')}: {error}"
                )

        if loaded_count == 0:
            logger.warning("Ни одна cookie не была добавлена.")
            return False

        logger.success(
            f"Добавлено cookies: {loaded_count}, пропущено: {skipped_count}. Обновляем сессию..."
        )
        self.driver.refresh()

        if self.is_authenticated():
            logger.success("Авторизация по кукам успешно подтверждена!")
            return True

        logger.warning("Сессия по кукам не подтвердилась, cookies устарели или неполны.")
        return False

    def ensure_authenticated(self):
        """
        Проверяет авторизацию, подгружает куки
        или запрашивает ручной вход, если кук нет.
        """
        # Сначала обязательно заходим на базовый домен VK
        self.driver.get("https://vk.ru")

        if self.is_authenticated():
            logger.success("Авторизация восстановлена из постоянного профиля Chrome.")
            return True

        if self.has_cookies() and self.load_cookies():
            return True

        logger.warning("Автоматическая авторизация не удалась. Требуется ручной вход.")
        self.save_cookies()
        return self.is_authenticated()
    
class VkScraper:
    """Сборник функций для процесса парсинга"""
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.driver = self.init_driver()

    @staticmethod
    def init_driver():
        """Инициализирует и возвращает драйвер"""
        chrome_options = default_chrome_settings.get_options()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def close_driver(self):
        """Закрывает драйвер"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def click_subscriptions(self):
        """
        Открывает подписки на необходимой странице
        """
        try:
            sub = self.driver.find_element(By.CSS_SELECTOR, "span.vkuiEllipsisText__host[title='Подписки']")
            sub.click()
            time.sleep(5)
        except Exception as e:
            error_msg = self.error_handler.selenium_error(e)
            logger.error(f"Ошибка открытия виджета: {error_msg}")

    def get_all_url_subscriptions(self):
        """
        Получаем все ссылки на подписки пользователя
        """
        # Открываем "Подписки"
        self.click_subscriptions()
        
        # Динамический скроллинг
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True: 
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2) 
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Собираем все подписки
        all_links = self.driver.find_elements(By.CSS_SELECTOR, "a.fans_idol_lnk")
        
        # Обрабатываем ссылки
        unique_urls = []
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                if href and href not in unique_urls:
                    # Убираем trackcode если есть
                    clean_url = href.split('?')[0]
                    unique_urls.append(clean_url)
            except:
                continue
        
        # Сохраняем в .txt
        log_dir = DATA_DIR / "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        with open(log_dir / "url_subscriptions.txt", "w", encoding="utf-8") as f:
            for url in unique_urls:
                f.write(url + "\n")
        
        return unique_urls

    @staticmethod
    def get_count_subscriptions(filepath: str) -> int:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return len([line for line in f if line.strip()])
        except:
            return 0

    def get_count_product(self):
        """
        Получаем количество товаров
        """
        try:
            product_elements = self.driver.find_elements(By.CSS_SELECTOR,
                "[data-testid='market_item']"
            )
            
            if product_elements:
                logger.info(f"Найдено товаров: {len(product_elements)}")

        except Exception as e:
            error_msg = self.error_handler.selenium_error(e)
            logger.error(f"Ошибка: {error_msg}")

    def validation_product_availability(self):
        """
        Валидация URL, сообщество ли это и есть ли там товары
        Возвращает True если есть вкладка "Товары"
        """
        try:
            button_products = self.driver.find_element(By.CSS_SELECTOR,
                "[data-testid='tab_content_market'], [data-testid*='market']"
            )

            # Если нашли 
            if button_products:
                logger.success("Вкладка 'Товары' найдена")
                return True
            else:
                logger.info("Вкладка 'Товары' не найдена")
                return False
            
        except:
            # Если не нашли ни одним способом
            logger.info(f"Вкладка 'Товары' отсутствует")
            return False

    def click_show_all_products(self):
        """
        Открывает кнопку товаров (Показать все)
        """
        try:
            # Ждем и кликаем на вкладку "Товары"
            wait = WebDriverWait(self.driver, 15)
            products_tab = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-tab="market"]'))
            )

            products_tab.click()
            time.sleep(2)
            
            # Теперь ищем кнопку "Показать все"
            show_all_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="groups_tabs_content_button_all"]')))
            
            # Прокручиваем к кнопке если нужно
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_all_button)
            time.sleep(0.5)
            
            # Кликаем
            show_all_button.click()
            
            # Ждем загрузки страницы со всеми товарами
            time.sleep(3)
            
        except Exception as e:
            error_msg = self.error_handler.selenium_error(e)
            logger.error(f"Ошибка при нажатии кнопки 'Показать все': {error_msg}")

    def download_product_image(image_url, save_path, filename=None):
            """
            Скачивает изображение товара и сохраняет его
            """
            if not image_url or not image_url.startswith('http'):
                logger.warning(f"Неверный URL изображения: {image_url}")
                return None
    
            try:
                # Создаем папку если нет
                os.makedirs(save_path, exist_ok=True)
                
                # Полный путь к файлу
                filepath = os.path.join(save_path, filename)
                
                # Скачиваем изображение
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(image_url, headers=headers, stream=True, timeout=10)
                response.raise_for_status()
                
                # Сохраняем файл
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
    
                return filepath
                
            except Exception as e:
                logger.error(f"Ошибка скачивания изображения {image_url}: {e}")
            return None

    def get_info_product(self, element):
        """
        Извлекает основную информацию о товаре из HTML элемента
        """
        product_info = {
            'name': '',
            'link': '',
            'price': '',
            'image_url': ''
        }
        
        try:
            # Название товара
            try:
                name_elem = element.find_element(By.CSS_SELECTOR, 
                    ".market_row_title, .product_title, .title, [class*='title'], [class*='name']"
                )
                product_info['name'] = name_elem.text.strip()
            except:
                # Пробуем найти в других местах
                product_info['name'] = ''
            
            # Ссылка на товар
            try:
                link_elem = element.find_element(By.TAG_NAME, "a")
                product_info['link'] = link_elem.get_attribute('href') or ''
            except:
                product_info['link'] = ''

            # Цена
            try:
                price_elem = element.find_element(By.CSS_SELECTOR,
                    ".market_row_price:not(.market_row_price_old)"
        )
        
                full_price_text = price_elem.text.strip()
                lines = [line.strip() for line in full_price_text.split('\n') if line.strip()]
        
                if lines:
                    product_info['price'] = lines[0]
                else:
                    product_info['price'] = ''
            
            except:
                product_info['price'] = ''

            # Картинка
            try:
                img_elem = element.find_element(By.TAG_NAME, "img")
                product_info['image_url'] = img_elem.get_attribute('src') or ''
                
                # Если нет src, пробуем data-src
                if not product_info['image_url']:
                    product_info['image_url'] = img_elem.get_attribute('data-src') or ''
            except:
                product_info['image_url'] = ''

        except Exception as e:
            error_msg = self.error_handler.selenium_error(e)
            logger.error(f"Ошибка извлечения информации: {error_msg}")
            product_info['error'] = str(e)
        
        return product_info