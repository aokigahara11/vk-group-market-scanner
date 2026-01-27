# main.py
from scraper.parser import main_process_scraper
from scraper.data.database import init_database_user, init_database_products

if __name__ == '__main__':
    init_database_user()
    init_database_products()
    main_process_scraper()
