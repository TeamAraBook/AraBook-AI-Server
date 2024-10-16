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

class BestBook:
    def __init__(self, isbn, title, author, publisher, publish_year, cover_url, description, best_rank):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.publisher = publisher
        self.publish_year = publish_year
        self.cover_url = cover_url
        self.description = description
        self.best_rank = best_rank
    
    def getBook(self):
        # self로 인스턴스 변수에 접근하여 Book 객체 반환
        return Book(self.isbn, self.title, self.author, self.publisher, self.publish_year, self.cover_url, self.description)


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
    
        
def get_best_sellers():
    
    url = "http://www.aladin.co.kr/ttb/api/ItemList.aspx"
    
    params = {
        'ttbkey': os.getenv("ALADIN_TTBKEY"),  # 환경변수에서 가져오거나 기본값 설정
        'QueryType': 'Bestseller',
        'MaxResults': 18,
        'start': 1,
        'SearchTarget': 'Book',
        'output': 'js',
        'Version': '20131101'
    }
    
    try:
        # API 요청 보내기
        response = requests.get(url, params=params)
        response.raise_for_status()  # HTTP 오류가 있으면 예외 발생
        data = response.json()  # JSON 응답을 파싱

        # 책 정보를 저장할 리스트
        book_list = []

        # 18개의 책 정보 추출
        for item in data['item']:
            
            # 필요한 정보 추출
            isbn = item['isbn13']
            publish_year = item['pubDate'][:4]  # 연도만 추출
            author = item['author']
            cover_url = item['cover'].replace("coversum", "cover500")  # cover500으로 치환
            description = item['description']
            publisher = item['publisher']
            title = item['title']
            best_rank = item['bestRank']
            
            book = BestBook(isbn, title, author, publisher, publish_year, cover_url, description, best_rank)
        
            # 리스트에 책 정보 추가
            book_list.append(book)

        return book_list

    except requests.exceptions.RequestException as e:
        print(f"HTTP 요청 중 오류 발생: {e}")
        return []