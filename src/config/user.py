# config/user.py
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / 'user.env'
load_dotenv(env_path)

USER = os.getenv('USER')