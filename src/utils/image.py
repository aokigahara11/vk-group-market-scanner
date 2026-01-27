# utils/image.py
from urllib.parse import urlparse
import os
import requests
import time
from utils.logger import logger

def download_product_image(image_url, save_path, filename=None):
    """
    Скачивает изображение товара и сохраняет его
    """
    if not image_url or not image_url.startswith('http'):
        logger.warning(f"Неверный URL изображения: {image_url}")
        return None

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

        return filepath
        
    except Exception as e:
        logger.error(f"Ошибка скачивания изображения {image_url}: {e}")
        return None