from dotenv import load_dotenv
import openai
import os

load_dotenv()


# OpenAI API Key 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
model_engine = "gpt-4"

# 카테고리 분류 함수
def classify_category(title, author, isbn, description, hashtags):
    base_prompt = """웹사이트에서 이 책의 정보를 검색해서 카테고리를 분류해줘.
    분류될 수 있는 카테고리의 대분류는 다음과 같아: 소설, 시/에세이, 자기계발, 인문, 여행, 철학, 사회, 과학, 역사, 판타지/무협지.
    각 대분류에 따른 소분류는 다음과 같아:
    소설 - 추리/스릴러, SF, 판타지, 공포, 영화/드라마 원작, 역사, 사랑, 청소년,
    시/에세이 - 시, 일상, 위로, 직업, 여행, 사랑/가족, 음식,
    자기계발 - 말하기/협상/프레젠테이션, 시간관리, 습관, 글쓰기, 독서, 사고법, 리더십, 직장인, 기획, 자존감/가치관,
    인문 - 인문학, 문명, 문화, 심리학, 인간/인류, 신화, 언어, 사랑, 영화, 예체능,
    여행 - 한국, 일본, 중국, 대만/홍콩, 미국, 호주, 남미, 동남아, 유럽, 중동/아프리카, 기타 국가,
    철학 - 동양, 서양, 예술/문화, 정치/경제,
    사회 - 사회학, 정치, 법, 젠더/페미니즘, 노동, 국가, 교육, 범죄, 환경, 세계, 사회문제, 미디어, 시사 매거진,
    과학 - 물리학/공학, 수학, 화학, 천문학/지구과학, 생명과학, 인체/뇌, 과학 매거진,
    역사 - 한국 고대사, 조선사, 한국 근현대사, 세계사,
    판타지/무협지 - 무협, 퓨전 판타지, 현대 판타지, 해외 판타지, 게임 판타지, 전쟁/대체역사, 라이트노벨.
    카테고리의 대분류는 하나만 가질 수 있고, 소분류는 여러 개 가질 수 있어.
    책의 카테고리를 분류해줘. 
    형식은 '대분류 - 소분류1, 소분류2, 소분류3'으로 해줘.

    예시:
    대분류 - 소분류1, 소분류2, 소분류3

    책 정보:
    - 제목: {title}
    - 저자: {author}
    - ISBN: {isbn}
    - 설명: {description}
    - 해시태그: {hashtags}
    """
    # 책 정보 포함
    full_prompt = f"{base_prompt}".format(title=title, author=author, isbn=isbn, description=description, hashtags=hashtags)
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {"role": "system", "content": "You are a helpful book-category-classifier."},
            {"role": "user", "content": full_prompt}
        ],
        max_tokens=100,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip().split("- ")[-1].split(", ")