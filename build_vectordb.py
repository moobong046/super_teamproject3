import os
import glob
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm

def build_full_vector_db():
    input_folder = "chunked_texts"
    db_folder = "chroma_db_qwen" 
    
    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
    documents = []
    
    for txt_path in txt_files:
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
            raw_chunks = content.split("-" * 50)
            for raw_chunk in raw_chunks:
                clean_chunk = raw_chunk.strip()
                if len(clean_chunk) > 20: 
                    doc = Document(page_content=clean_chunk)
                    documents.append(doc)

    print(f"🎯 총 {len(documents)}개의 전체 텍스트 조각을 임베딩합니다!")
    
    embedding_model = HuggingFaceEmbeddings(
        model_name="Qwen/Qwen3-Embedding-0.6B",
        encode_kwargs={'normalize_embeddings': True}
    )
    
    vector_db = Chroma(persist_directory=db_folder, embedding_function=embedding_model)
    
    # 50개씩 묶어서 끝까지 달립니다!
    batch_size = 50 
    for i in tqdm(range(0, len(documents), batch_size), desc="전체 데이터 DB 굽는 중"):
        batch = documents[i : i + batch_size]
        vector_db.add_documents(batch)
        
    print(f"\n✅ 대성공! 전체 데이터가 '{db_folder}'에 완벽하게 저장되었습니다!")

if __name__ == "__main__":
    build_full_vector_db()