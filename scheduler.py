import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database_conn import get_all_member_ids
from database_conn import insert_book_info_to_db
from database_conn import get_book_id_by_isbn
from database_conn import insert_best_sellers

from book_info import get_best_sellers
from category_classifier import classify_category

from crawling import get_hashtags

from chroma_manager import ChromaManager

chroma_manager = ChromaManager(persist_directory="./chroma_db", collection_name="books")

async def run_recommendations_for_all_members():
    # MySQL에서 전체 member_id 가져오기
    member_ids = get_all_member_ids()
    print("Running recommendations for all members...")
    # 각 멤버에 대해 도서 추천 함수 실행
    for member_id in member_ids:
        chroma_manager.recommend_book(member_id)
    print("Recommendations for all members have been completed.")
    
# 베스트셀러 업데이트 작업 정의
async def best_sellers_update_task():
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


# 스케줄러 설정 함수
def start_scheduler():
    scheduler = AsyncIOScheduler()

    # 매일 오전 0시 1분에 스케줄러 실행
    scheduler.add_job(run_recommendations_for_all_members, 'cron', hour=0, minute=1)
    
    # # 스케줄러에 작업 추가 (매 1분마다 실행)
    scheduler.add_job(best_sellers_update_task, 'interval', minutes=1)
    # 스케줄러에 작업 추가 (매달 1일마다 실행)
    # scheduler.add_job(best_sellers_update_task, 'cron', day=1, hour=0, minute=0)
    
    # 스케줄러 시작
    scheduler.start()

    # # 백그라운드에서 스케줄러가 실행되도록 유지
    # try:
    #     while True:
    #         time.sleep(2)
    # except (KeyboardInterrupt, SystemExit):
    #     scheduler.shutdown()