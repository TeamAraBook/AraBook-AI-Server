from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

# 도서 검색 결과 페이지에서 해시태그 정보 가져오기
def get_hashtags(isbn):
    search_url = f"https://search.kyobobook.co.kr/search?keyword={isbn}"
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(search_url)
    
    time.sleep(3)  # 페이지가 완전히 로드될 때까지 잠시 대기

    # 해시태그 리스트 추출
    try:
        hashtags_elements = driver.find_elements(By.CSS_SELECTOR, 'a.tag')
        hashtags = [tag.text for tag in hashtags_elements]
        hashtags = [tag.replace("#", "") for tag in hashtags]   # 해시태그 기호 제거
        category = hashtags[0]  # 첫 번째 해시태그는 카테고리로 사용
        hashtags = list(set(hashtags[1:]))[1:]  # 중복 제거 후 두 번째 해시태그부터 사용

        return category, hashtags
    
    except Exception as e:
        print(f"해시태그를 찾는 중 오류 발생: {e}")
        return None, None
    
    driver.quit()

# 예시 실행
# isbn = "9788925538297"
isbn = '9788954699372'
category, hashtags = get_hashtags(isbn)
print(f"{isbn}\n카테고리: {category}, 해시태그 목록: {hashtags}")