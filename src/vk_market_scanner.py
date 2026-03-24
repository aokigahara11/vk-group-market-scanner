# src/vk_market_scanner.py
from scraper.parser import main_process_scraper
from database.database import init_database_user, init_database_products

class VkMarketScanner:
    """Основной класс для сканирования рынка групп VK."""

    def __init__(self):
        """Инициализация сканера."""
        self._init_databases()

    def _init_databases(self):
        """Инициализация баз данных."""
        init_database_user()
        init_database_products()

    def run(self):
        """Запуск процесса сканирования."""
        main_process_scraper()