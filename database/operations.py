from database.connection import create_connection, close_connection
import pymysql

def add_child_to_db(child_name, birth):
    # TABLE child에 아동 record 추가
    connection = create_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO child (name, birth)
    VALUES (%s, %s)
    """ 
    values = (child_name, birth)

    try:
        cursor.execute(query, values)
        connection.commit()
        # print(">> 어린이 데이터 추가 완료 (database.operations.add_child_to_db)")
    except pymysql.MySQLError as e:
        print(f">> 기록 삽입 실패 {e} (database.operations.add_child_to_db)")
    finally:
        cursor.close()
        close_connection(connection)

def save_symptom_to_db(child_name, symptom, description=""):
    # MySQL DB에 증상 데이터 저장
    connection = create_connection()
    cursor = connection.cursor()
    
    query = """
    INSERT INTO symptom_reports (child_name, symptom, description) 
    VALUES (%s, %s, %s)
    """
    values = (child_name, symptom, description)
    
    try:
        cursor.execute(query, values)
        connection.commit()
        # print(">> 증상이 데이터베이스에 성공적으로 저장되었습니다. (database.operations.save_symptom_to_db)")
    except pymysql.MySQLError as e:
        print(f"Failed to insert record into MySQL table {e} (database.operations.save_symptom_to_db)")
    finally:
        cursor.close()
        close_connection(connection)

def fetch_all_children():
    # npcb_db의 TABLE child에 등록된 아이 조회
    connection = create_connection()
    cursor = connection.cursor()

    query = "SELECT * FROM child"

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            print(f">> fetched info: {row} (database.operations.fetch_all_children)")
    except pymysql.MySQLError as e:
        print(f"Failed to fetch records from MySQL table {e} (database.operations.fetch_all_children)")
    finally:
        cursor.close()
        close_connection(connection)
        return results

def fetch_symptom_history(child_name):
    # MySQL DB에서 모든 증상 조회
    connection = create_connection()
    cursor = connection.cursor()
    
    query = "SELECT * FROM symptom_reports WHERE child_name = %s"
    
    try:
        cursor.execute(query, (child_name))
        results = cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f">> Failed to fetch records from MySQL table {e} (database/operations.py)")
    finally:
        cursor.close()
        close_connection(connection)
        return results;

def delete_child(child_name):
    # TABLE child에서 지정한 이름의 아이 정보 삭제, TABLE symptoms에서 증상정보 삭제
    connection = create_connection()
    cursor = connection.cursor()

    query_reports = "DELETE FROM symptom_reports WHERE child_name = %s;"
    query_child = "DELETE FROM child WHERE name = %s;"

    try:
        cursor.execute(query_reports, (child_name))
        cursor.execute(query_child, (child_name))
        connection.commit()
    except pymysql.MySQLError as e:
        print(f">> Failed to delete records")
    finally:
        cursor.close()
        close_connection(connection)

def update_child(name_to_update, updated_name, updated_birth):
    # TABLE child에서 지정한 이름의 아이 정보 수정
    connection = create_connection()
    cursor = connection.cursor()

    query = "UPDATE child SET name = %s, birth = %s WHERE name = %s"

    try:
        cursor.execute(query, (updated_name, updated_birth, name_to_update))
        connection.commit()
    except pymysql.MySQLError as e:
        print(f">> Failed to delete records")
    finally:
        cursor.close()
        close_connection(connection)
    pass