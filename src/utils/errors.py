# utils/errors.py
import re

def selenium_error(exc):
    """Упрощает Selenium ошибку для логирования"""
    error_str = str(exc)
    
    # Ищем селектор
    match = re.search(r'selector":"(.+?)"', error_str)
    if match:
        selector = match.group(1)
        return f"Элемент не найден: {selector[:50]}..."
    
    # Или берем первую значимую строку
    lines = error_str.split('\n')
    for line in lines:
        if line.strip() and "Session info:" not in line:
            return line[:80] + ("..." if len(line) > 80 else "")
    
    return "Ошибка Selenium"