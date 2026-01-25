import sys
import os
import time
import requests
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.user import USER
from config.setting import default_chrome_settings

chrome_options = default_chrome_settings.get_options()

# Запускаем драйвер с настройками
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Исполняем скрипт для маскировки под обычного пользователя
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def click_subscriptions():
    """
    Открывает подписки на необходимой странице
    """
    try:
        sub = driver.find_element(By.CSS_SELECTOR, "span.vkuiEllipsisText__host[title='Подписки']")
        sub.click()
        time.sleep(5)
    except Exception as e:
        print(f"Ошибка открытия виджета: {e}")

def get_all_url_subscriptions():
    """
    Получаем все ссылки на подписки пользователя
    """
    # Открываем "Подписки"
    click_subscriptions()
    
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
    print(f"Найдено ссылок: {len(all_links)}")
    
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

def get_count_product():
    """
    Получаем количество товаров
    """
    try:
        product_elements = driver.find_elements(By.CSS_SELECTOR, 
            "[data-testid='market_item']"
        )
        
        if product_elements:
            print(f"Найдено товаров: {len(product_elements)}")

    except Exception as e:
        print(f"Ошибка: {e}")

def validation_product_availability():
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
            print("✓ Вкладка 'Товары' найдена")
            return True
        else:
            print("✗ Вкладка 'Товары' не найдена")
            return False
        
    except Exception as e:
        # Если не нашли ни одним способом
        print(f"Вкладка 'Товары' отсутствует: {e}")
        return False

def click_show_all_products():
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
        print(f"Ошибка при нажатии кнопки 'Показать все': {e}")

def get_info_product(element):
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
        print(f"Ошибка извлечения информации: {e}")
        product_info['error'] = str(e)
    
    return product_info

def download_product_image(image_url, save_path, filename=None):
    """
    Скачивает изображение товара и сохраняет его
    """
    if not image_url or not image_url.startswith('http'):
        print(f"Неверный URL изображения: {image_url}")
        return None

    try:
        # Создаем папку если нет
        os.makedirs(save_path, exist_ok=True)
        
        # Генерируем имя файла если не указано
        if not filename:
            # Берем последнюю часть URL
            parsed_url = urlparse(image_url)
            url_path = parsed_url.path
            filename = os.path.basename(url_path)
            
            # Если нет расширения, добавляем .jpg
            if not filename or '.' not in filename:
                filename = f"product_{int(time.time())}.jpg"
        
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
        print(f"✗ Ошибка скачивания изображения {image_url}: {e}")
        return None

