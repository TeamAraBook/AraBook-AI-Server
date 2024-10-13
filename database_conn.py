import pymysql
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import os
import ast

load_dotenv()

def connect_to_db():
    """SSH 터널을 통해 MySQL 데이터베이스에 연결하고 연결 객체를 반환합니다."""
    ssh_tunnel_host_address = os.environ['SSH_TUNNEL_HOST_ADDRESS']
    ssh_tunnel_host_port = int(os.environ['SSH_TUNNEL_HOST_PORT'])
    ssh_username = os.environ['SSH_USERNAME']
    ssh_private_key = os.environ['SSH_PRIVATE_KEY']
    mysql_server_host = os.environ['MYSQL_SERVER_HOST']
    db_username = os.environ['DB_USERNAME']
    db_password = os.environ['DB_PASSWORD']
    db_database_name = os.environ['DB_DATABASE_NAME'] 

    try:
        tunnel = SSHTunnelForwarder(
            (ssh_tunnel_host_address, ssh_tunnel_host_port),  # SSH 서버 주소 및 IP
            ssh_username=ssh_username,          # SSH 사용자 이름
            ssh_pkey=ssh_private_key,           # SSH 개인 키 파일 경로
            remote_bind_address=(mysql_server_host, 3306)  # MySQL 서버 주소 및 포트
        )
        tunnel.start()  # SSH 터널 시작

        # MySQL 연결
        connection = pymysql.connect(
            host='127.0.0.1',  # 로컬 호스트
            user=db_username,  # MySQL 사용자 이름
            password=db_password,  # MySQL 비밀번호
            db=db_database_name,  # 사용할 데이터베이스 이름
            charset='utf8mb4',
            port=tunnel.local_bind_port,  # SSH 터널로 로컬 포트 바인딩
            cursorclass=pymysql.cursors.DictCursor
        )

        return connection, tunnel  # 연결 객체와 터널 반환
    except Exception as e:
        print(f"Error connecting to the database: {e}")

def get_sub_category_id(connection, category_name):
    """주어진 카테고리 이름에 대한 서브 카테고리 ID를 조회합니다."""
    try:
        with connection.cursor() as cursor:
            sql = "SELECT sub_category_id FROM sub_categories WHERE sub_category_name = %s"
            cursor.execute(sql, (category_name,))
            result = cursor.fetchone()
            if result:
                return result['sub_category_id']
            else:
                return None
    except Exception as e:
        print(f"Error finding sub_category_id: {e}")
        return None

def insert_book_info_to_db(book, category_names, hashtags):
    """책 정보를 데이터베이스에 삽입합니다."""
    connection, tunnel = connect_to_db()  # 연결 생성
    if not connection:
        print("Failed to connect to the database.")
        return
      
    if isinstance(category_names, str):
        category_names = ast.literal_eval(category_names) 

    try:
        with connection.cursor() as cursor:
            # 1. `books` 테이블에 책 정보를 삽입
            sql_book = """
                INSERT INTO books (isbn, title, author, description, publisher, cover_url, publish_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title), author = VALUES(author), description = VALUES(description),
                publisher = VALUES(publisher), cover_url = VALUES(cover_url), publish_year = VALUES(publish_year)
            """
            cursor.execute(sql_book, (
                book.isbn,
                book.title,
                book.author,
                book.description,
                book.publisher,
                book.cover_url,
                book.publish_year
            ))

            # 삽입된 책의 ID를 가져오기
            book_id = cursor.lastrowid

            # 2. `hashtags` 테이블에 해시태그 삽입
            for hashtag in hashtags:
                sql_hashtag = """
                    INSERT INTO hashtags (name) VALUES (%s)
                    ON DUPLICATE KEY UPDATE name = VALUES(name)
                """
                cursor.execute(sql_hashtag, (hashtag,))
                hashtag_id = cursor.lastrowid

                # 3. `book_hashtag_mappings` 테이블에 book_id와 hashtag_id 매핑
                sql_book_hashtag_mapping = """
                    INSERT INTO book_hashtag_mappings (book_id, hashtag_id)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE book_id = VALUES(book_id), hashtag_id = VALUES(hashtag_id)
                """
                cursor.execute(sql_book_hashtag_mapping, (book_id, hashtag_id))

            # 4. `sub_category_id` 조회 및 `book_sub_category_mappings` 테이블에 book_id와 sub_category_id 매핑
            for category_name in category_names:
                sub_category_id = get_sub_category_id(connection, category_name)  # 변경된 부분
                if sub_category_id:
                    sql_book_sub_category_mapping = """
                        INSERT INTO book_sub_category_mappings (book_id, sub_category_id)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE book_id = VALUES(book_id), sub_category_id = VALUES(sub_category_id)
                    """
                    cursor.execute(sql_book_sub_category_mapping, (book_id, sub_category_id))
                else:
                    print(f"Sub-category not found for category: {category_name}")

            # 모든 작업이 성공했으면 커밋
            connection.commit()
            print("Transaction committed successfully")

    except Exception as e:
        print(f"Error occurred, rolling back. Error: {e}")
        connection.rollback()
    finally:
        connection.close()  # 연결 종료
        tunnel.close()  # 터널 종료

def get_member_preferences(member_id):
    """사용자의 선호 서브 카테고리 ID 리스트를 반환합니다."""
    connection, tunnel = connect_to_db()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT sc.sub_category_name
                FROM member_sub_category_selections ms
                JOIN sub_categories sc ON ms.sub_category_id = sc.sub_category_id
                WHERE ms.member_id = %s
                """

            cursor.execute(sql, (member_id,))
            results = cursor.fetchall()
            return [row['sub_category_name'] for row in results]
    except Exception as e:
        print(f"Error occurred, Error: {e}")
    finally:
        connection.close()
        tunnel.close()

def get_book_id_by_isbn(isbn: str) -> int:
    connection, tunnel = connect_to_db()  # 연결 생성
    if not connection:
        print("Failed to connect to the database.")
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT book_id FROM books WHERE isbn = %s", (isbn,))
            result = cursor.fetchone()
            if result:
                return result['book_id']
            else:
                return None  # 책이 없는 경우
    except Exception as e:
        print(f"Error occurred, Error: {e}")
    finally:
        connection.close()
        tunnel.close()

    return result[0] if result else None


def save_recommendation(member_id, book_id, recommendation_date):
    """추천된 책 정보를 daily_book_id_recommendations 테이블에 저장합니다."""
    connection, tunnel = connect_to_db()
    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO daily_book_id_recommendations (member_id, book_id, recommendation_date)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (member_id, book_id, recommendation_date))
            connection.commit()
    finally:
        connection.close()
        tunnel.close()
