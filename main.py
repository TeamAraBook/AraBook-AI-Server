from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI
from pydantic import BaseModel
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

app = FastAPI()

# OpenAI API Key 설정
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 요청 본문을 처리하기 위한 Pydantic 모델
class MessageRequest(BaseModel):
    prompt: str
    model: str = "gpt-4o-mini"
    max_tokens: int = 100

# POST 요청을 처리하는 엔드포인트
@app.post("/generate/")
async def generate_text(request: MessageRequest):
    try:
        # OpenAI API 호출
        response = client.chat.completions.create(model=request.model,
        messages=[{"role": "user", "content": request.prompt}],
        max_tokens=request.max_tokens)
        # API 응답에서 텍스트 부분 추출
        generated_text = response.choices[0].message.content
        return {"generated_text": generated_text}
    except Exception as e:
        return {"error": str(e)}
