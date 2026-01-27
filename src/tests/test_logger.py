# tests/test_logger.py
from rich.console import Console
from rich.theme import Theme
from datetime import datetime

class Logger:
    def __init__(self):
        self.console = Console(theme=Theme({
            "info": "cyan",
            "warning": "yellow",
            "error": "bold red",
            "success": "bold green",
            "timestamp": "grey50"
        }))

    def log(self, level, message, **kwargs):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        level_styles = {
            "INFO": "info",
            "WARNING": "warning", 
            "ERROR": "error",
            "SUCCESS": "success",
        }
        
        level_clean = level.upper().rstrip(':')
        style = level_styles.get(level_clean, "info")
        
        self.console.print(
            f"[timestamp][{timestamp}][/timestamp] "
            f"[{style}][{level_clean:}][/{style}] "
            f"{message}",
            **kwargs
        )
    
    def info(self, message):
        self.log("INFO", message)
        
    def warning(self, message):
        self.log("WARNING", message)
        
    def error(self, message):
        self.log("ERROR", message)
        
    def success(self, message):
        self.log("SUCCESS", message)

logger = Logger()
logger.info("Парсер запущен!")
logger.warning("Проверьте подключение к интернету")
logger.error("Ошибка соединения с базой данных")
logger.success("Товары успешно сохранены")