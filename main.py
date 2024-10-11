from dotenv import load_dotenv
import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

from category_classifier import classify_category
from crawling import get_hashtags

import chromadb
from chromadb.config import Settings

# .env 파일에서 환경 변수 로드
load_dotenv()

app = FastAPI()

# OpenAI API Key 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
model_engine = "gpt-4"

persist_directory = "./chroma_db"

# 디렉토리가 없으면 생성
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)

# Chroma 클라이언트 초기화
client = chromadb.PersistentClient(path=persist_directory)
# 기존 컬렉션 가져오기
collection = client.get_collection("books")

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

class BookRequest(BaseModel):
    title: str
    author: str
    isbn: str
    description: str
    mainCategory: str
    subCategory: list
    hashtags: list

# 기본 엔드포인트
@app.post("/generate/")
async def generate_text(request: GenerateMessageRequest):
    try:
        # OpenAI API 호출
        response = openai.Completion.create(model=request.model,
        messages=[{"role": "user", "content": request.prompt}],
        max_tokens=request.max_tokens)
        # API 응답에서 텍스트 부분 추출
        generated_text = response.choices[0].message.content
        return {"generated_text": generated_text}
    except Exception as e:
        return {"error": str(e)}
    
# 카테고리 분류 엔드포인트
@app.post("/classify/")
async def classify(request: ClassifyMessageRequest):
    try:
        # 카테고리 분류 함수 호출
        category = classify_category(request.title, request.author, request.isbn, request.description, request.max_tokens)
        return {"title": request.title, "category": category}

    except Exception as e:
        return {"error": str(e)}
    
# 도서 정보 크롤링 엔드포인트
@app.post("/crawl/")
async def crawl(request: CrawlMessageRequest):
    try:
        # 도서 정보 크롤링 함수 호출
        return {"isbn": request.isbn, "hashtags": get_hashtags(request.isbn)}
    except Exception as e:
        return {"error": str(e)}
    
# 책 정보 추가 엔드포인트
@app.post("/add_book/")
async def add_book(request: BookRequest):
    metahash_string = ', '.join(request.hashtags)
    metasub_string = ', '.join(request.subCategory)
    # Chroma DB에 책 정보 추가
    collection.add(
        documents=[request.description], 
        metadatas=[{"title": request.title, "author": request.author, "isbn": request.isbn, "hashtags": metahash_string, "mainCategory": request.mainCategory, "subCategory": metasub_string}], 
        ids=[request.isbn]  # 고유 ID
    )

    return {"message": "책 정보가 추가되었습니다."}

# 책 정보 조회 엔드포인트
@app.get("/get_book/{isbn}")
async def get_book(isbn: str):
    # 'books' 컬렉션 가져오기
    collection = client.get_collection("books")
    
    # ISBN으로 책 정보 검색
    results = collection.query(
        query_texts=[isbn],  # ISBN을 쿼리 텍스트로 사용
        n_results=1  # 최대 1개의 결과만 가져옴
    )

    if results["documents"]:
        # 결과가 있을 경우
        book_info = results["metadatas"][0][0]  # 첫 번째 메타데이터 가져오기
        # return {
        #     "title": book_info["title"],
        #     "author": book_info["author"],
        #     "isbn": book_info["isbn"],
        #     "description": results["documents"][0],  # 문서 내용 (설명)
        #     "hashtags": book_info["hashtags"].split(', '),  # 해시태그 리스트로 변환
        #     "mainCategory": book_info["mainCategory"],
        #     "subCategory": book_info["subCategory"].split(', ')  # 소분류 리스트로 변환
        # }
        return book_info
    else:
        # 결과가 없는 경우
        raise HTTPException(status_code=404, detail="책 정보를 찾을 수 없습니다.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)