import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import chromadb
import os

from book_info import get_book_info_by_isbn 
from chroma_manager import ChromaManager
from category_classifier import classify_category
from crawling import get_hashtags
from scheduler import start_scheduler
from database_conn import insert_book_info_to_db

# .env 파일에서 환경 변수 로드
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting scheduler...")
    start_scheduler()
    print("Scheduler started.")
    yield
    print("Stopping scheduler...")

app = FastAPI(lifespan=lifespan)

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