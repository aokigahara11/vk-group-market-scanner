# utils/scraper.py
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import logger
from utils.errors import ErrorHandler

class VkScraper:
    def __init__(self):
        self.error_handler = ErrorHandler()

    def click_subscriptions(self, driver):
        """
        Открывает подписки на необходимой странице
        """
        try:
            sub = driver.find_element(By.CSS_SELECTOR, "span.vkuiEllipsisText__host[title='Подписки']")
            sub.click()
            time.sleep(5)
        except Exception as e:
            error_msg = self.error_handler.selenium_error(e)
            logger.error(f"Ошибка открытия виджета: {error_msg}")

    def get_all_url_subscriptions(self, driver):
        """
        Получаем все ссылки на подписки пользователя
        """
        # Открываем "Подписки"
        self.click_subscriptions(driver)
        
        # Динамический скроллинг
        last_height = driver.execute_script("return document.body.scrollHeight") 
        while True: 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") 
            time.sleep(2) 
            new_height = driver.execute_script("return document.body.scrollHeight") 
            if new_height == last_height:
                break
            last_height = new_height
        
        # Собираем все подписки
        all_links = driver.find_elements(By.CSS_SELECTOR, "a.fans_idol_lnk")
        
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
        os.makedirs("src/data/logs", exist_ok=True)
        
        with open("src/data/logs/url_subscriptions.txt", "w", encoding="utf-8") as f:
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

    def get_count_product(self, driver):
        """
        Получаем количество товаров
        """
        try:
            product_elements = driver.find_elements(By.CSS_SELECTOR, 
                "[data-testid='market_item']"
            )
            
            if product_elements:
                logger.info(f"Найдено товаров: {len(product_elements)}")

        except Exception as e:
            error_msg = self.error_handler.selenium_error(e)
            logger.error(f"Ошибка: {error_msg}")

    def validation_product_availability(self, driver):
        """
        Валидация URL, сообщество ли это и есть ли там товары
        Возвращает True если есть вкладка "Товары"
        """
        try:
            button_products = driver.find_element(By.CSS_SELECTOR, 
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

    def click_show_all_products(self, driver):
        """
        Открывает кнопку товаров (Показать все)
        """
        try:
            # Ждем и кликаем на вкладку "Товары"
            wait = WebDriverWait(driver, 15)
            products_tab = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-tab="market"]'))
            )

            products_tab.click()
            time.sleep(2)
            
            # Теперь ищем кнопку "Показать все"
            show_all_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="groups_tabs_content_button_all"]')))
            
            # Прокручиваем к кнопке если нужно
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_all_button)
            time.sleep(0.5)
            
            # Кликаем
            show_all_button.click()
            
            # Ждем загрузки страницы со всеми товарами
            time.sleep(3)
            
        except Exception as e:
            error_msg = self.error_handler.selenium_error(e)
            logger.error(f"Ошибка при нажатии кнопки 'Показать все': {error_msg}")

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