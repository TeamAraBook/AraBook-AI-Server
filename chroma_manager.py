from datetime import datetime, timedelta
import os
from typing import List, Optional
from fastapi import HTTPException
from database_conn import get_book_id_by_isbn, get_member_preferences, save_recommendation
from langchain_openai import OpenAIEmbeddings
import chromadb

class ChromaManager:
    def __init__(self, persist_directory: str, collection_name: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_collection(collection_name)
        self.embedding_function = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    def add_book(self, book, main_category: str, sub_category: Optional[List[str]], hashtags: Optional[List[str]]) -> str:
        # ISBN으로 책 정보가 이미 존재하는지 확인
        existing_books = self.collection.get(ids=[book.isbn])

        if existing_books["ids"]:  # 이미 존재하는 경우
            return "이미 존재하는 책 정보입니다."

        # None 값 처리
        sub_category = sub_category if sub_category is not None else []
        hashtags = hashtags if hashtags is not None else []

        sub_category_str = ', '.join(sub_category)  # 리스트를 문자열로 변환
        hashtags_str = ', '.join(hashtags)          # 리스트를 문자열로 변환

        # 임베딩을 생성할 텍스트 조합
        embed_text = f"title: {book.title}\nauthor: {book.author}\ndescription: {book.description}\nmain_category: {main_category}\nsub_category: {sub_category_str}\nhashtags: {hashtags_str}"

        # 단일 문서에 대해 임베딩 생성
        embeddings = self.embedding_function.embed_documents([embed_text])

        # Chroma DB에 책 정보 추가
        self.collection.add(
            documents=[book.description],
            metadatas=[{
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "hashtags": hashtags_str,
                "mainCategory": main_category,
                "subCategory": sub_category_str,
            }],
            embeddings=[embeddings[0]],  # 첫 번째 임베딩만 사용
            ids=[book.isbn]
        )
        return "책 정보가 성공적으로 추가되었습니다."

    
    def delete_book(self, isbn: str) -> str:
        # ISBN으로 책 정보가 존재하는지 확인
        existing_books = self.collection.get(ids=[isbn])

        if not existing_books["ids"]:
            return "존재하지 않는 책 정보입니다."
        
        # Chroma DB에서 책 정보 삭제
        self.collection.delete(ids=[isbn])
        return "책 정보가 성공적으로 삭제되었습니다."
    
    def get_book(self, isbn: str) -> dict:
        # ISBN으로 책 정보가 존재하는지 확인
        existing_books = self.collection.get(ids=[isbn])

        if not existing_books["ids"]:
            raise HTTPException(status_code=404, detail="존재하지 않는 책 정보입니다.")

        # 책 정보 반환
        metadata = existing_books["metadatas"][0]  # 메타데이터 가져오기
        return {
            "title": metadata["title"],
            "author": metadata["author"],
            "isbn": metadata["isbn"],
            "description": existing_books["documents"][0],  # 문서에서 설명 가져오기
            "hashtags": metadata["hashtags"],
            "mainCategory": metadata["mainCategory"],
            "subCategory": metadata["subCategory"],
        }
    
    def recommend_book(self, member_id: str) -> str:
        preferences = get_member_preferences(member_id)
        if not preferences:
            return "No preferences found for the member."

        query = " ".join(preferences)
        embedding = self.embedding_function.embed_query(query)

        results = self.collection.query(query_embeddings=embedding, n_results=1)
        
        if results['documents'] and results['metadatas']:
            # 메타데이터에서 ISBN 가져오기
            metadata = results['metadatas'][0][0]  # 이중 리스트에서 첫 번째 메타데이터 가져오기
            isbn = metadata['isbn']
            
            # ISBN으로 MySQL에서 book_id를 검색합니다.
            book_id = get_book_id_by_isbn(isbn)  # 새로운 함수 추가 필요
            if not book_id:
                return "No book ID found for the given ISBN."
            
            recommendation_date = (datetime.now() + timedelta(days=1)).date()
            
            # MySQL에 book_id를 저장합니다.
            save_recommendation(member_id, book_id, recommendation_date)
            
            return f"Recommended book ID: {book_id}"
        else:
            return "No book found for the given preferences."



