from dotenv import load_dotenv
import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

import os
from book_info import get_book_info_by_isbn 
from book_info import get_best_sellers

from chroma_manager import ChromaManager

from category_classifier import classify_category

from crawling import get_hashtags

import chromadb

from database_conn import insert_book_info_to_db
from database_conn import get_book_id_by_isbn
from database_conn import insert_best_sellers

# .env 파일에서 환경 변수 로드
load_dotenv()

app = FastAPI()

# 스케줄러 초기화
scheduler = BackgroundScheduler()

# 실행할 작업 정의
def best_sellers_update_task():
    best_sellers_list_from_aladin = get_best_sellers()
    best_sellers_for_save = []
    
    # 각 책의 정보를 검사
    for best_book in best_sellers_list_from_aladin:
        isbn = best_book.isbn  # Book 객체의 isbn 가져오기
        book_id = get_book_id_by_isbn(isbn)
        title = best_book.title
        author = best_book.author
        description = best_book.description
        best_rank = best_book.best_rank
        
        # ISBN이 데이터베이스에 존재하는지 확인
        if book_id is None:
            # ISBN이 없을 경우 책 정보를 데이터베이스에 추가
            hashtags = get_hashtags(isbn)
            
            
            main_category, sub_category = classify_category(title, author, isbn, description, hashtags)
            # MySQL에 책 정보 추가
            insert_book_info_to_db(best_book.getBook(), category_names=sub_category, hashtags=hashtags)
            # Chroma DB에 책 정보 추가
            chroma_manager.add_book(best_book.getBook(), main_category, sub_category, hashtags)

        else:
            # ISBN이 이미 있으면 필요 시 업데이트 (생략 가능)
            print(f"책 {title} (ISBN: {isbn})는 이미 데이터베이스에 있습니다.")
        
        best_seller = {
                'isbn': isbn,
                'best_rank': best_rank
        }
        
        best_sellers_for_save.append(best_seller)
    
    for test in best_sellers_for_save:
        print(test['isbn'])
        print(test['best_rank'])
    
    insert_best_sellers(best_sellers_for_save)
    print("스케줄러 종료")
        
# # 스케줄러에 작업 추가 (매 1분마다 실행)
# scheduler.add_job(best_sellers_update_task, 'interval', minutes=1)

# 스케줄러에 작업 추가 (매달 1일마다 실행)
scheduler.add_job(best_sellers_update_task, 'cron', day=1, hour=0, minute=0)

# 스케줄러 시작
scheduler.start()

# OpenAI API Key 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# Chroma DB 설정
persist_directory = "./chroma_db"
chroma_manager = ChromaManager(persist_directory=persist_directory, collection_name="books")

# 디렉토리가 없으면 생성
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)
    

# 요청 본문을 처리하기 위한 Pydantic 모델
class GenerateMessageRequest(BaseModel):
    prompt: str
    model: str = "gpt-4"
    max_tokens: int = 100

class ClassifyMessageRequest(BaseModel):
    title: str
    author: str
    isbn: str
    description: str

class CrawlMessageRequest(BaseModel):
    isbn: str
    max_tokens: int = 100

class AddBookRequest(BaseModel):
    isbn: str

class BookRequest(BaseModel):
    title: str
    author: str
    isbn: str
    description: str
    mainCategory: str
    subCategory: list
    hashtags: list

class RecommendRequest(BaseModel):
    member_id: int

# 기본 엔드포인트
@app.post("/generate")
async def generate_text(request: GenerateMessageRequest):
    try:
        # OpenAI API 호출
        response = openai.ChatCompletion.create(
            model=request.model,
            messages=[{"role": "user", "content": request.prompt}],
            max_tokens=request.max_tokens
        )
        # API 응답에서 텍스트 부분 추출
        generated_text = response.choices[0].message.content
        return {"generated_text": generated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 카테고리 분류 엔드포인트
@app.post("/classify")
async def classify(request: ClassifyMessageRequest):
    try:
        hashtags = get_hashtags(request.isbn)  # ISBN을 이용해 해시태그 가져오기

        # 카테고리 분류 함수 호출
        main, sub = classify_category(request.title, request.author, request.isbn, request.description, hashtags)
        return {"title": request.title, "main_category": main, "sub_category": sub}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 도서 정보 크롤링 엔드포인트
@app.post("/crawl")
async def crawl(request: CrawlMessageRequest):
    try:
        # 도서 정보 크롤링 함수 호출
        hashtags = get_hashtags(request.isbn)
        return {"isbn": request.isbn, "hashtags": hashtags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 책 정보 추가 엔드포인트
@app.post("/add-book")
async def add_book(request: AddBookRequest):
    try:
        # ISBN으로 책 정보 가져오기
        book = get_book_info_by_isbn(request.isbn)
        hashtags = get_hashtags(request.isbn)
        main_category, sub_category = classify_category(book.title, book.author, book.isbn, book.description, hashtags)
        
        # MySQL에 책 정보 추가
        insert_book_info_to_db(book, category_names=sub_category, hashtags=hashtags)
        # Chroma DB에 책 정보 추가
        message = chroma_manager.add_book(book, main_category, sub_category, hashtags)
        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# 책 정보 삭제 엔드포인트
@app.post("/delete-book")
async def delete_book(request: AddBookRequest):
    try:
        # Chroma DB에서 책 정보 삭제
        message = chroma_manager.delete_book(request.isbn)
        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# 책 정보 조회 엔드포인트
@app.get("/get-book")
async def get_book(isbn: str):
    try:
        # Chroma DB에서 책 정보 조회
        book_info = chroma_manager.get_book(isbn)
        return book_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# 도서 추천 엔드포인트
@app.post("/recommend")
async def recommend(request: RecommendRequest):
    # 도서 추천 요청 처리
    try:
        result = chroma_manager.recommend_book(request.member_id)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)