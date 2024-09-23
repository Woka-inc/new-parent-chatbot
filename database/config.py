import os
from dotenv import load_dotenv

load_dotenv()

# MySQL 설정값 (환경 변수로 불러오기)
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_USER = 'root'
DB_PASSWORD = 'your password here'
DB_NAME = 'npcb_db'