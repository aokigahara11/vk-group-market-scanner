# scraper/data/database.py
import sqlite3
import datetime
from typing import Optional, Tuple, Any
import os
from pathlib import Path

from config.user import USER

if not os.path.exists('src/data/database'):
    os.makedirs('src/data/database')

# Создаем постоянные соединения для основных БД
connect = sqlite3.connect('src/data/database/database.db', check_same_thread=False)
cursor = connect.cursor()

# Включаем поддержку внешних ключей
connect.execute("PRAGMA foreign_keys = ON")

# ==== Таблица профиля таргет-пользователя ====

def init_database_user():
    """Инициализирует таблицу пользователя"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            link TEXT, 
            subscriptions INTEGER
        )
    ''')
    connect.commit()

def add_info_user(link, subscriptions):
    """Добавляет или обновляет информацию о пользователе"""
    cursor.execute('''
        INSERT OR REPLACE INTO user (link, subscriptions) 
        VALUES (?, ?)
    ''', (link, subscriptions))
    connect.commit()

# ==== Таблица товаров ====

def init_database_products():
    """Инициализирует таблицу товаров"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            link TEXT UNIQUE,
            price INTEGER,
            community TEXT
        )
    ''')
    connect.commit()

def add_info_product(name, link, price, community):
    """Добавляет или обновляет информацию о товаре"""
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO products (name, link, price, community) 
            VALUES (?, ?, ?, ?)
        ''', (name, link, price, community))
        connect.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении товара: {e}")
        return False