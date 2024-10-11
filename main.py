from dotenv import load_dotenv
import openai
from fastapi import FastAPI
from pydantic import BaseModel
import os

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


# 기본 함수
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)