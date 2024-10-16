import time
from apscheduler.schedulers.background import BackgroundScheduler
from chroma_manager import ChromaManager
from database_conn import get_all_member_ids

def run_recommendations_for_all_members():
    # MySQL에서 전체 member_id 가져오기
    member_ids = get_all_member_ids()
    chroma_manager = ChromaManager(persist_directory="./chroma_db", collection_name="books")
    print("Running recommendations for all members...")
    # 각 멤버에 대해 도서 추천 함수 실행
    for member_id in member_ids:
        chroma_manager.recommend_book(member_id)
    print("Recommendations for all members have been completed.")

# 스케줄러 설정 함수
def start_scheduler():
    scheduler = BackgroundScheduler()

    # 매일 오후 3시 5분에 스케줄러 실행
    scheduler.add_job(run_recommendations_for_all_members, 'cron', hour=0, minute=1)
    # 스케줄러 시작
    scheduler.start()

    # 백그라운드에서 스케줄러가 실행되도록 유지
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
