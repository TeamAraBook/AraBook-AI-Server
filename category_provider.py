from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

# 카테고리 아이템을 추출하고 텍스트 파일로 저장하는 함수
def get_category_items_and_save():
    search_url = f"https://kyobobook.co.kr"
    
    # 웹 드라이버 설정
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(search_url)
    
    time.sleep(2)  # 페이지가 완전히 로드될 때까지 대기
    
    # 카테고리 목록을 저장할 리스트
    all_categories = []

    try:
        driver.find_element(By.CSS_SELECTOR, '.btn_anb').click()
        print("btn_anb 버튼 클릭")
        buttons = driver.find_elements(By.CSS_SELECTOR, '.btn_fold')

        # 각 버튼을 클릭하여 리스트 추출
        for i, button in enumerate(buttons):
            try:
                # 버튼 클릭
                button.click()
                time.sleep(2)
                
                # 리스트 요소 추출
                category_elements = driver.find_elements(By.CSS_SELECTOR, 'li.category_item .category_link')
                
                # 카테고리 텍스트 추출
                categories = [element.text for element in category_elements]
                # null 제거
                categories = list(filter(None, categories))
                
                # 추출한 카테고리를 전체 리스트에 추가
                all_categories.extend(categories)

                # 다시 버튼 클릭해서 닫기
                button.click()
                time.sleep(1)

            except Exception as e:
                print(f"버튼 {i+1}에서 오류 발생: {e}")
        
        # 텍스트 파일로 추가 저장
        with open("categories.txt", "w", encoding="utf-8") as file:
            for category in all_categories:
                file.write(category + "\n")
        
        print(f"모든 카테고리가 'categories.txt' 파일에 저장되었습니다.")

    except Exception as e:
        print(f"카테고리 정보를 가져오는 중 오류 발생: {e}")
    
    driver.quit()

# 예시 실행
get_category_items_and_save()
