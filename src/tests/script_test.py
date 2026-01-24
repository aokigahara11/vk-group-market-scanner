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

driver.get(USER)
time.sleep(10)
 
def click_subscriptions():
    """
    Открывает подписки на необходимой странице
    """
    try:
        sub = driver.find_element(By.CSS_SELECTOR, "span.vkuiEllipsisText__host[title='Подписки']")
        print(f"Нашли элемент: {sub.get_attribute('outerHTML')[:100]}")
        sub.click()
        time.sleep(5)
        print('Кнопка "Подписки" успешно открыта!')
    except Exception as e:
        print(f"Ошибка открытия виджета: {e}")

def get_all_url_subscriptions(driver):
    """
    Получаем все ссылки на подписки пользователя
    """
    # Открываем "Подписки"
    click_subscriptions()
    
    print("Начинаем скроллинг...")
    
    # Динамический скроллинг
    last_height = driver.execute_script("return document.body.scrollHeight") 
    while True: 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") 
        time.sleep(2) 
        new_height = driver.execute_script("return document.body.scrollHeight") 
        if new_height == last_height:
            break
        print("Прокрутка завершена") 
        last_height = new_height
        print("Появился новый контент, прокручиваем дальше")
    
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
    
    print(f"Уникальных ссылок: {len(unique_urls)}")
    
    # Сохраняем в .txt
    os.makedirs("scr/data/logs", exist_ok=True)
    
    with open("scr/data/logs/url_subscriptions.txt", "w", encoding="utf-8") as f:
        for url in unique_urls:
            f.write(url + "\n")
    
    print(f"Ссылки сохранены в scr/data/logs/url_subscriptions.txt")
    
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

def get_info_communities(link):
    """
    Собирает информацию о сообществе
    """
    info = {
        'name': '',
        'link': link,
        'subscribers': 0,
        'reviews': None
    }
    
    try:
        # Переходим на страницу сообщества
        driver.get(link)
        time.sleep(2)
        
        print(f"Собираем информацию: {link}")
        
        # Имя группы
        try:
            name_elem = driver.find_element(By.CSS_SELECTOR, "h1.page_name")
            # Берем только текст до первого span (если есть)
            name_text = name_elem.text
            # Убираем возможные лишние пробелы и переводы строк
            info['name'] = name_text.split('\n')[0].strip()
            print(f"{info['name']}")
        except:
            print("Не нашли название")
        
        # Подписчики
        try:
            subscribers_elem = driver.find_element(By.CSS_SELECTOR, "span.header_count")
            sub_text = subscribers_elem.text
            
            # Убираем пробелы и преобразуем в число
            sub_text_clean = sub_text.replace(' ', '').replace('\u202f', '').replace('\xa0', '')
            
            try:
                info['subscribers'] = int(sub_text_clean)
                print(f"{info['subscribers']}")
            except ValueError:
                print(f" '{sub_text}' в число")
                
        except:
            print("Не нашли количество подписчиков")
        
        # Средний балл
        try:
            # Ищем по data-testid
            rating_elem = driver.find_element(By.CSS_SELECTOR, 
                "[data-testid='rating-layout-indicator']"
            )
            rating_text = rating_elem.text.strip()
            
            # Заменяем запятую на точку для float
            rating_text = rating_text.replace(',', '.')
            
            try:
                info['reviews'] = float(rating_text)
                print(f"{info['reviews']}")
            except ValueError:
                print(f"Не удалось преобразовать рейтинг '{rating_text}'")
                
        except:
            # Если не нашли по data-testid, пробуем другие варианты
            try:
                # Ищем по классу
                rating_elem = driver.find_element(By.CSS_SELECTOR, 
                    ".vkitRatingLayout__indicator, [class*='rating'], [class*='Rating']"
                )
                rating_text = rating_elem.text.strip().replace(',', '.')
                
                try:
                    info['reviews'] = float(rating_text)
                    print(f"{info['reviews']}")
                except:
                    pass
                    
            except:
                # Если совсем не нашли
                print("Рейтинг не найден")
                info['reviews'] = None
        
    except Exception as e:
        print(f"❌ Ошибка при сборе информации: {e}")
        info['error'] = str(e)
    
    return info

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

def click_show_all_products(link):
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
        print('Перешли на вкладку "Товары"')
        time.sleep(2)
        
        # Теперь ищем кнопку "Показать все"
        show_all_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="groups_tabs_content_button_all"]')))
        
        # Прокручиваем к кнопке если нужно
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_all_button)
        time.sleep(0.5)
        
        # Кликаем
        show_all_button.click()
        print('Кнопка "Показать все" успешно нажата!')
        
        # Ждем загрузки страницы со всеми товарами
        time.sleep(3)
        
    except Exception as e:
        print(f"Ошибка при нажатии кнопки 'Показать все': {e}")

def save_link_communities(number):
    """
    Получает ссылку по номеру из файла

    """
    with open("scr/data/logs/url_subscriptions.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        
        if 1 <= number <= len(lines):
            selected_link = lines[number - 1]
            return selected_link
    
def get_info_product(product_element):
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
            name_elem = product_element.find_element(By.CSS_SELECTOR, 
                ".market_row_title, .product_title, .title, [class*='title'], [class*='name']"
            )
            product_info['name'] = name_elem.text.strip()
        except:
            # Пробуем найти в других местах
            try:
                # Иногда название в атрибуте alt у картинки
                img_elem = product_element.find_element(By.TAG_NAME, "img")
                product_info['name'] = img_elem.get_attribute('alt') or ''
            except:
                product_info['name'] = ''
        
        # Ссылка на товар
        try:
            link_elem = product_element.find_element(By.TAG_NAME, "a")
            product_info['link'] = link_elem.get_attribute('href') or ''
        except:
            product_info['link'] = ''

        # Цена
        try:
            price_elem = product_element.find_element(By.CSS_SELECTOR,
                ".market_row_price, .product_price, .price, [class*='price'], [class*='cost']"
            )
            product_info['price'] = price_elem.text.strip()
        except:
            product_info['price'] = ''

        # Картинка
        try:
            img_elem = product_element.find_element(By.TAG_NAME, "img")
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
    
    save_path = 'src/data/images'

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
        
        print(f"✓ Изображение сохранено: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"✗ Ошибка скачивания изображения {image_url}: {e}")
        return None

                
