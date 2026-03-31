from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def test_rag_search():
    db_folder = "chroma_db_qwen"
    
    print("🧠 Qwen 다국어 모델 로딩 중... (이번엔 캐시에서 1초 만에 불러옵니다!)")
    # 1. 아까와 똑같은 번역기(임베딩 모델)를 준비합니다.
    embedding_model = HuggingFaceEmbeddings(
        model_name="Qwen/Qwen3-Embedding-0.6B",
        encode_kwargs={'normalize_embeddings': True},
        model_kwargs={'device': 'cuda' if __import__('torch').cuda.is_available() else 'cpu'}
    )
    
    print("📂 10시간 동안 구워낸 Vector DB에 접속합니다...")
    # 2. 저장해둔 DB 폴더를 연결합니다.
    vector_db = Chroma(persist_directory=db_folder, embedding_function=embedding_model)
    
    print("-" * 50)
    # 🌟 3. 테스트해볼 한국어 질문 (원하는 부품 스펙 질문으로 자유롭게 바꿔보세요!)
    query = "H5TQ2G83DFR 부품의 작동 온도(Operating Temperature) 범위가 어떻게 돼?"
    print(f"❓ 사용자 질문: {query}")
    print("-" * 50)
    
    # 4. 수천 개의 영어 조각 중, 한국어 질문과 '의미'가 가장 비슷한 3개(k=3)를 찾아옵니다.
    results = vector_db.similarity_search(query, k=3)
    
    # 5. 찾은 결과를 예쁘게 출력합니다.
    for i, doc in enumerate(results):
        print(f"🥇 [Top {i+1} 매칭 결과]")
        print(doc.page_content)
        print("=" * 60 + "\n")

if __name__ == "__main__":
    test_rag_search()