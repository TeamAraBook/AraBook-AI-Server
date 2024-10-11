from dotenv import load_dotenv
import requests
import os

# .env 파일 로드
load_dotenv()

# Book 클래스 정의
class Book:
    def __init__(self, isbn, title, author, publisher, publish_year, cover_url, description):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.publisher = publisher
        self.publish_year = publish_year
        self.cover_url = cover_url
        self.description = description


# 알라딘 API로부터 책 정보를 조회하는 함수
def get_book_info_by_isbn(isbn):
    # 알라딘 상품 조회 API URL
    url = 'http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx'

    # API 요청 파라미터 설정
    params = {
        'ttbkey': os.getenv("ALADIN_TTBKEY"),
        'itemIdType': 'ISBN',
        'ItemId': isbn,
        'output': 'JS',
        'Version': '20131101'
    }

    # API 요청 보내기
    response = requests.get(url, params=params)

    # 요청 성공 시 JSON 데이터 처리
    if response.status_code == 200:
        data = response.json()

        # 첫 번째 결과 추출
        if 'item' in data:
            item = data['item'][0]

            # 필요한 정보 추출
            isbn = item['isbn13']
            publish_year = item['pubDate'][:4]  # 연도만 추출
            author = item['author']
            cover_url = item['cover'].replace("coversum", "cover500")  # cover500으로 치환
            description = item['description']
            publisher = item['publisher']
            title = item['title']

            # Book 객체 생성 및 반환
            return Book(isbn, title, author, publisher, publish_year, cover_url, description)
        else:
            print("책 정보를 찾을 수 없습니다.")
    else:
        print(f"요청 실패: {response.status_code}")