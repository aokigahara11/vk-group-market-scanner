# utils/logger.py
import os
from datetime import datetime
from rich.console import Console
from rich.theme import Theme

class Logger:
    def __init__(self):
        self.console = Console(theme=Theme({
            "info": "blue",
            "step": "blue", 
            "warning": "yellow",
            "error": "red",
            "success": "green",
            "timestamp": "#B7B7B7",
            "message": "white"
        }))
        
        # Автоматически создаем лог-файл
        self.log_file = "src/data/logs/logs.txt"
        self._init_log_file()
    
    def _init_log_file(self):
        """Создает файл и пишет начало работы"""
        try:
            os.makedirs("src/data/logs", exist_ok=True)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\nНачало работы скрипта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except:
            pass  # Если не удалось - ничего страшного
    
    def _write_to_file(self, message):
        """Просто записывает сообщение в файл"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except:
            pass  # Тихий фейл
    
    def log(self, level, message, **kwargs):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        level_styles = {
            "INFO": "info",
            "STEP": "step",
            "WARNING": "warning", 
            "ERROR": "error",
            "SUCCESS": "success"
        }
        
        level_clean = level.upper().rstrip(':')
        style = level_styles.get(level_clean, "info")
        
        # Вывод в консоль
        self.console.print(
            f"[timestamp][{timestamp}][/timestamp] "
            f"[{style}][{level_clean}][/{style}] "
            f"[message]{message}[/message]",
            **kwargs
        )
        
        # Запись в файл (просто текст, без тегов)
        file_msg = f"[{timestamp}] [{level_clean}] {message}"
        self._write_to_file(file_msg)
    
    def info(self, message):
        self.log("INFO", f"ℹ {message}")
    
    def step(self, message):
        self.log("STEP", f"» {message}")
        
    def warning(self, message):
        self.log("WARNING", f"! {message}")
        
    def error(self, message):
        self.log("ERROR", f"✗ {message}")
        
    def success(self, message):
        self.log("SUCCESS", f"✓ {message}")


# Глобальный логгер
logger = Logger()