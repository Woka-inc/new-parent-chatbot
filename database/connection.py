import pymysql
from database.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

def create_connection():
    connection = None
    try:
        # print(">> MySQL에 연결하겠소 (database/connection.py)")
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8',
            read_timeout=60 # with the read_timeout parameter being set the connection error is being thrown out
        )
        # print(">> MySQL 데이터베이스에 성공적으로 연결되었습니다. (database/connection.py)")
    except pymysql.MySQLError as e:
        print(f">> MySQL DB Error: '{e}' (database/connection.py)")
    
    return connection

def close_connection(connection):
    if connection:
        connection.close()
        # print(">> MySQL 연결이 닫혔습니다. (database/connection.py)")