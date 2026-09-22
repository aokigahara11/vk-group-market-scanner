from database import core
from src.utils.logger import logger


class DatabaseProducts:
    """Класс для сохранения и обработки данных товаров."""

    @staticmethod
    def init_database_products():
        """Инициализирует таблицу товаров."""
        cursor = core.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                name TEXT NOT NULL,
                link TEXT UNIQUE,
                price INTEGER,
                community TEXT
            )
        ''')
        core.conn.commit()

    @staticmethod
    def add_info_product(name, link, price, community):
        """Добавляет или обновляет информацию о товаре."""
        cursor = core.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO products (name, link, price, community)
                VALUES (?, ?, ?, ?)
            ''', (name, link, price, community))
            core.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара: {e}")
            return None