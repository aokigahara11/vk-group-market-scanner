# config/setting.py

from selenium.webdriver.chrome.options import Options

# Настройки для Chrome
class ChromeSettings:
    def __init__(self):
        self.chrome_options = Options()

        # Отключаем логирование DevTools
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Скрываем автоматизацию
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # Дополнительные настройки для удобства
        self.chrome_options.add_argument("--start-maximized")  # Запуск в развернутом окне
        self.chrome_options.add_argument("--disable-notifications")  # Отключаем уведомления
        
    def get_options(self):
        """Получить объект настроек"""
        return self.chrome_options

# Создаем глобальный экземпляр с настройками по умолчанию
default_chrome_settings = ChromeSettings()