# MySQL 설정값 (환경 변수로 불러오기)
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_USER = 'root'
DB_NAME = 'npcb_db'

DB_PASSWORD = input("DB 비밀번호: ")
with open("./database/config.py", "a") as config_file:
    config_file.write(f"\nDB_PASSWORD = '{DB_PASSWORD}'")