# 1. 베이스 이미지 설정
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필요한 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements.txt

# 4. 애플리케이션 소스 복사
COPY . .

# 5. FastAPI 앱 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
