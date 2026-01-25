# utils/driver.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config.setting import default_chrome_settings

def init_driver():
    """Инициализирует и возвращает драйвер"""
    chrome_options = default_chrome_settings.get_options()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def close_driver(driver):
    """Закрывает драйвер"""
    if driver:
        driver.quit()