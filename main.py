from dotenv import load_dotenv
import openai
from fastapi import FastAPI
from pydantic import BaseModel
import os
from book_info import get_book_info_by_isbn
from database_conn import insert_book_info_to_db

from category_classifier import classify_category
from crawling import get_hashtags

# .env 파일에서 환경 변수 로드
load_dotenv()

app = FastAPI()

# OpenAI API Key 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
model_engine = "gpt-4"


# 요청 본문을 처리하기 위한 Pydantic 모델
class GenerateMessageRequest(BaseModel):
    prompt: str
    model: str = "gpt-4o-mini"
    max_tokens: int = 100

class ClassifyMessageRequest(BaseModel):
    title: str
    author: str
    isbn: str
    description: str
    max_tokens: int = 100

class CrawlMessageRequest(BaseModel):
    isbn: str
    max_tokens: int = 100

class AddBookRequest(BaseModel):
    isbn: str
        
# 카테고리 분류 함수
@app.post("/classify/")
async def classify(request: ClassifyMessageRequest):
    try:
        # 카테고리 분류 함수 호출
        category = classify_category(request.title, request.author, request.isbn, request.description, request.max_tokens)
        return {"title": request.title, "category": category}

    except Exception as e:
        return {"error": str(e)}
    
# 도서 정보 크롤링 함수
@app.post("/crawl/")
async def crawl(request: CrawlMessageRequest):
    try:
        # 도서 정보 크롤링 함수 호출
        return {"isbn": request.isbn, "hashtags": get_hashtags(request.isbn)}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/add-book/")
async def add_book(request: AddBookRequest):
    try:
        book = get_book_info_by_isbn(request.isbn)
        category = classify_category(book.title, book.author, book.isbn, book.description, 100)
        hashtag = get_hashtags(book.isbn)
        print(category)
        insert_book_info_to_db(book, category_names=category, hashtags=hashtag)
        return "200 OK"
    except Exception as e:
        return {"error": str(e)}
        
        

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)