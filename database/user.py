from database import core
from src.utils.logger import logger


class DatabaseUser:
    """Класс для обработки данных целевого пользователя."""

    @staticmethod
    def init_database_user():
        """Инициализирует таблицу пользователя."""
        cursor = core.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                link TEXT,
                subscriptions INTEGER
            )
        ''')
        core.conn.commit()

    @staticmethod
    def add_info_user(link, subscriptions):
        """Добавляет или обновляет информацию о пользователе."""
        cursor = core.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO user (link, subscriptions)
                VALUES (?, ?)
            ''', (link, subscriptions))
            core.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")
            return None