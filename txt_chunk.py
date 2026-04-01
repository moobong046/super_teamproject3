import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_and_chunk_datasheet(text, component_name):
    # 1. 🧹 텍스트 정제 (노이즈 제거)
    # 우리가 파싱할 때 넣었던 페이지 구분선 제거
    clean_text = re.sub(r'================ \[페이지 \d+\] ================', '', text)
    clean_text = re.sub(r'================ \[Page \d+\] ================', '', clean_text)
    
    # 데이터시트 특유의 문서 번호 및 페이지 번호 패턴 제거 (예: DocID031239 Rev 4, 11/84)
    clean_text = re.sub(r'DocID\d+ Rev \d+', '', clean_text)
    clean_text = re.sub(r'\n\d+/\d+\n', '\n', clean_text) 
    
    # 불필요하게 여러 번 들어간 줄바꿈을 하나로 축소
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

    # 2. ✂️ 스마트 청킹 (Recursive Splitting)
    # 데이터시트는 표가 통째로 들어가야 하므로 chunk_size를 넉넉하게 잡는 것이 좋습니다.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,       # 한 조각당 약 800자
        chunk_overlap=150,    # 문맥이 끊기지 않게 이전 조각의 150자를 겹쳐서 가져옴
        separators=["\n\n", "\n", " ", ""] # 문단 자르기 -> 줄 자르기 순서로 시도
    )

    # 텍스트를 조각(Chunk)들로 쪼개기
    chunks = text_splitter.split_text(clean_text)
    
    # 3. 🏷️ 메타데이터(부품 이름)와 함께 반환
    final_chunks = []
    for chunk in chunks:
        # 각 조각의 맨 앞에 부품 이름을 꼬리표처럼 붙여줍니다. (RAG 성능 수직 상승의 비결!)
        context_injected_chunk = f"[부품명: {component_name}]\n{chunk.strip()}"
        final_chunks.append(context_injected_chunk)
        
    return final_chunks

# =====================================================================
# 🧪 테스트 실행
# (앞서 추출한 텍스트 파일 중 하나를 읽어와서 테스트해 봅니다)
if __name__ == "__main__":
    # 파일명 예시: parsed_texts 폴더 안의 텍스트 파일
    test_file_path = "parsed_texts/imu_ASM330LHH.txt" 
    
    try:
        with open(test_file_path, "r", encoding="utf-8") as f:
            sample_text = f.read()
            
        # 함수 실행 (부품 이름은 파일명에서 유추해서 넣어줍니다)
        resulting_chunks = clean_and_chunk_datasheet(sample_text, "ASM330LHH")
        
        print(f"✅ 총 {len(resulting_chunks)}개의 청크(조각)로 완벽하게 분할되었습니다!\n")
        
        # 첫 번째와 두 번째 조각만 미리보기
        for i in range(min(2, len(resulting_chunks))):
            print(f"📦 [Chunk {i+1}]")
            print(resulting_chunks[i])
            print("-" * 50)
            
    except FileNotFoundError:
        print("텍스트 파일을 찾을 수 없습니다. 경로를 확인해주세요!")