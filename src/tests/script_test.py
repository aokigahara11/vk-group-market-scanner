import sys
import os
import time

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

def save_count_url():
    """
    Сохранение количество ссылок
    """
    with open("scr/data/logs/url_subscriptions.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        count = len(lines)
        
        return count

def save_count_product():
    """
    Сохранение количество товаров
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
