import requests
from bs4 import BeautifulSoup

# 도서 검색 결과 페이지에서 해시태그 정보 가져오기
def get_hashtags(isbn):
    standard_category = load_categories(file_path="categories.txt")
    search_url = f"https://search.kyobobook.co.kr/search?keyword={isbn}"
    
    try:
        # 페이지 요청
        response = requests.get(search_url)
        response.raise_for_status()  # 요청이 실패하면 예외 발생

        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 해시태그 리스트 추출
        hashtags_elements = soup.select('a.tag')  # CSS 선택자로 해시태그 요소 찾기
        hashtags = [tag.text.replace("#", "") for tag in hashtags_elements]
        hashtags = list(set(hashtags))  # 중복 제거

        # 표준 카테고리에 포함된 해시태그 제거
        hashtags = [tag for tag in hashtags if tag not in standard_category]

        return hashtags
    
    except Exception as e:
        print(f"해시태그를 찾는 중 오류 발생: {e}")
        return None

# 카테고리 파일에서 카테고리 리스트 가져오기
def load_categories(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            categories = [line.strip() for line in file.readlines()]
        return categories
    except Exception as e:
        print(f"카테고리 파일을 읽는 중 오류 발생: {e}")
        return []
