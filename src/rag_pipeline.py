import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
# 🌟 변경점 1: 구글 대신 OpenAI 라이브러리를 불러옵니다!
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# ⚠️ 보안 알림: 실제 키는 타인에게 노출되지 않도록 주의하세요!
os.environ["OPENAI_API_KEY"] = ""

def run_final_rag():
    db_folder = "chroma_db_qwen"
    
    # 1. 든든한 검색 엔진(Vector DB) 세팅
    print("🔍 Vector DB(Qwen)를 준비합니다...")
    embedding_model = HuggingFaceEmbeddings(
        model_name="Qwen/Qwen3-Embedding-0.6B",
        encode_kwargs={'normalize_embeddings': True},
        model_kwargs={'device': 'cuda' if __import__('torch').cuda.is_available() else 'cpu'}
    )
    vector_db = Chroma(persist_directory=db_folder, embedding_function=embedding_model)
    
    # 🌟 변경점 2: 요리사를 OpenAI의 GPT-4o-mini로 교체합니다!
    print("🤖 GPT-4o-mini 모델을 호출합니다...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1) 

    # 3. 요리사에게 줄 레시피(프롬프트) 작성
    prompt_template = """
    당신은 전자 부품 데이터시트를 분석하는 친절하고 전문적인 엔지니어입니다.
    아래에 제공된 [검색된 문서 조각]만을 바탕으로 사용자의 [질문]에 한국어로 답변해 주세요.
    만약 문서에 질문에 대한 답이 없다면, 억지로 지어내지 말고 "제공된 문서에서는 해당 스펙을 찾을 수 없습니다."라고 솔직하게 답변하세요.

    [검색된 문서 조각]
    {context}

    [질문]
    {question}
    
    답변:
    """
    prompt = PromptTemplate.from_template(prompt_template)

    # 4. 질문 던지기!
    print("-" * 50)
    query = "H5TQ2G83DFR 부품의 작동 온도(Operating Temperature) 범위가 어떻게 돼?"
    print(f"❓ 질문: {query}")
    print("-" * 50)
    
    # 5. DB에서 재료 꺼내오기
    results = vector_db.similarity_search(query, k=3)
    context_text = "\n\n".join([doc.page_content for doc in results])
    
    # 6. GPT에게 전달하여 답변 생성!
    print("👨‍🍳 GPT가 영어 문서를 읽고 한국어 답변을 생성 중입니다...\n")
    chain = prompt | llm
    answer = chain.invoke({"context": context_text, "question": query})
    
    print("🌟 [최종 AI 답변] 🌟")
    print(answer.content)
    print("=" * 50)

if __name__ == "__main__":
    run_final_rag()