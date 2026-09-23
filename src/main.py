# main.py
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.product import DatabaseProducts
from database.user import DatabaseUser
from src.scraper.parser import main_process_scraper

def main():
    DatabaseUser.init_database_user()
    DatabaseProducts.init_database_products()
    main_process_scraper()

if __name__ == '__main__':
    main()
