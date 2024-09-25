from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

# 도서 검색 결과 페이지에서 해시태그 정보 가져오기
def get_hashtags(isbn):
    standard_category = load_categories(file_path="categories.txt")
    search_url = f"https://search.kyobobook.co.kr/search?keyword={isbn}"
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(search_url)
    
    time.sleep(3)  # 페이지가 완전히 로드될 때까지 잠시 대기

    # 해시태그 리스트 추출
    try:
        hashtags_elements = driver.find_elements(By.CSS_SELECTOR, 'a.tag')
        hashtags = [tag.text for tag in hashtags_elements]
        hashtags = [tag.replace("#", "") for tag in hashtags]   # 해시태그 기호 제거
        hashtags = list(set(hashtags))  # 중복 제거
        categories = []
        for tag in hashtags:
            if tag in standard_category:
                categories.append(tag)
                hashtags.remove(tag)

        return categories, hashtags
    
    except Exception as e:
        print(f"해시태그를 찾는 중 오류 발생: {e}")
        return None, None
    
    driver.quit()

# 카테고리 파일에서 카테고리 리스트 가져오기
def load_categories(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            categories = [line.strip() for line in file.readlines()]
        return categories
    except Exception as e:
        print(f"카테고리 파일을 읽는 중 오류 발생: {e}")
        return []

# # 예시 실행
# isbn = "9788925538297"
# # isbn = '9788954699372'
# category, hashtags = get_hashtags(isbn)
# print(f"{isbn}\n카테고리: {category}, 해시태그 목록: {hashtags}")