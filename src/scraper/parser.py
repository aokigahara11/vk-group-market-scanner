# scraper/parser.py
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from utils.driver import init_driver
from utils.scraper import (
    get_all_url_subscriptions,
    validation_product_availability, 
    click_show_all_products,
    get_info_product,
    get_count_subscriptions
)
from utils.image import download_product_image
from config.user import USER
from scraper.data.database import add_info_user, add_info_product
from utils.logger import logger
from utils.errors import selenium_error

def main_process_scraper():
    """
    Главная функция парсера товаров
    """
    driver = init_driver()
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. Заходим на профиль целевого пользователя
        logger.step("Переходим на профиль пользователя...")
        driver.get(USER)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 2. Заходим в подписки и выгружаем URL
        logger.step("Получаем все ссылки на подписки...")
        urls = get_all_url_subscriptions(driver)
        
        if not urls:
            logger.error("Не найдено подписок для парсинга")
            return
        
        # 3. Проверяем существование файла с ссылками
        file_path = "src/data/logs/url_subscriptions.txt"
        if not os.path.exists(file_path):
            logger.error(f"Файл {file_path} не найден")
            return
        
        count_subscriptions = get_count_subscriptions(file_path)
        add_info_user(USER, count_subscriptions)

        # 4. Читаем ссылки из файла и обрабатываем построчно
        logger.step("Начинаем обработку подписок...")
        
        with open(file_path, "r", encoding="utf-8") as f:
            urls_from_file = [line.strip() for line in f if line.strip()]
        
        processed_count = 0
        with_products_count = 0
        total_products = 0
        
        for i, url in enumerate(urls_from_file, 1):
            logger.step(f"Обрабатываем ссылку {i}/{len(urls_from_file)}")
            logger.info(f"URL: {url}")
            
            try:
                # Переходим по ссылке
                driver.get(url)
                # Ждем загрузки основной части страницы
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Валидация: проверяем есть ли вкладка "Товары"
                logger.step("Проверяем наличие товаров...")
                validation = validation_product_availability(driver)
                
                if validation:
                    with_products_count += 1
                    
                    # Нажимаем "Показать все" товары
                    try:
                        click_show_all_products(driver)
                    except Exception as e:
                        error_msg = selenium_error(e)
                        logger.error(f"Не удалось открыть все товары: {error_msg}")
                        # Пробуем продолжить сбор с текущей страницы
                    
                    # Ждем загрузки товаров
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
                            "[data-testid='market_item'], .market_item, .market_row, .product_item"
                        )))
                    except TimeoutException:
                        logger.warning("Товары не загрузились за отведенное время")
                        processed_count += 1
                        continue
                    
                    # Получаем количество товаров
                    logger.info("Получаем количество товаров...")
                    product_elements = driver.find_elements(By.CSS_SELECTOR,
                        "[data-testid='market_item'], .market_item, .market_row, .product_item"
                    )
                    
                    count = len(product_elements)
                    logger.info(f"Найдено товаров: {count}")
                    total_products += count
                    
                    if count > 0:
                        # Собираем информацию о каждом товаре
                        logger.step(f"Собираем информацию о {count} товарах...")
                        
                        for j in range(count):
                            # Обновляем элементы каждый раз, так как страница может меняться
                            try:
                                product_elements = driver.find_elements(By.CSS_SELECTOR,
                                    "[data-testid='market_item'], .market_item, .market_row, .product_item"
                                )
                                
                                if j >= len(product_elements):
                                    break
                                    
                                product_element = product_elements[j]
                                
                                # Прокручиваем к элементу для загрузки контента
                                driver.execute_script(
                                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                                    product_element
                                )
                                
                                # Даем время на загрузку контента
                                try:
                                    wait.until(EC.visibility_of(product_element))
                                except:
                                    pass
                                
                                # Получаем информацию о товаре
                                product_info = get_info_product(product_element)
                                
                                name_product = product_info.get('name', '-')
                                link_product = product_info.get('link', '-')
                                price_product = product_info.get('price', '-')

                                community_url = url
                                community_name = "unknown"
                                if community_url:
                                    community_name = community_url.split('vk.com/')[-1].split('?')[0]

                                add_info_product(name_product, link_product, price_product, community_name)
                                
                                # Скачиваем изображение если есть
                                image_url = product_info.get('image_url')
                                if image_url and image_url.startswith('http'):
                                        
                                    filename = f"{community_name}_{j+1}_{int(time.time())}.jpg"
           
                                    # 3. Вызываем функцию с корректными параметрами
                                    download_product_image(
                                        image_url=image_url,
                                        save_path="src/data/images",
                                        filename=filename
                                    )
                                    
                            except (StaleElementReferenceException, NoSuchElementException) as e:
                                logger.warning(f"Элемент товара {j+1} стал устаревшим или не найден, пропускаем...")
                                continue
                            except Exception as e:
                                error_msg = selenium_error(e)
                                logger.error(f"Ошибка при обработке товара {j+1}: {error_msg}")
                                continue
                                
                    else:
                        logger.warning("Товары не найдены на странице")
                        
                else:
                    logger.info("Сообщество не имеет товаров. Пропускаем...")
                
                processed_count += 1
                
                # Небольшая пауза между запросами
                if i < len(urls_from_file):
                    time.sleep(1)  # Минимальная пауза
                    
            except Exception as e:
                error_msg = selenium_error(e)
                logger.error(f"Ошибка при обработке ссылки {url}: {error_msg}")
                continue
        
        # 5. Итоги работы
        logger.success("Парсинг завершен!")
        logger.info(f"Всего обработано: {processed_count} сообществ")
        logger.info(f"С товарами: {with_products_count} сообществ")
        logger.info(f"Всего товаров собрано: {total_products}")
        
    except Exception as e:
        logger.error(f"Критическая ошибка в главном процессе: {e}")
        
    finally:
        logger.info("Завершение работы...")