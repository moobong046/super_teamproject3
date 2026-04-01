import os
import glob
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 아까 테스트했던 완벽한 청킹 함수
def clean_and_chunk_datasheet(text, component_name):
    # 노이즈 청소
    clean_text = re.sub(r'================ \[페이지 \d+\] ================', '', text)
    clean_text = re.sub(r'================ \[Page \d+\] ================', '', clean_text)
    clean_text = re.sub(r'DocID\d+ Rev \d+', '', clean_text)
    clean_text = re.sub(r'\n\d+/\d+\n', '\n', clean_text) 
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

    # 랭체인 스플리터 설정 (황금 비율)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(clean_text)
    
    # 꼬리표(메타데이터) 달기
    final_chunks = []
    for chunk in chunks:
        final_chunks.append(f"[부품명: {component_name}]\n{chunk.strip()}")
        
    return final_chunks

# 2. 39개 파일을 한 번에 처리하는 메인 함수
def process_all_chunks():
    input_folder = "parsed_texts"       # 원본 텍스트가 있는 폴더
    output_folder = "chunked_texts"     # 청킹된 결과물이 저장될 새 폴더
    
    # 새 폴더 만들기
    os.makedirs(output_folder, exist_ok=True)
    
    # 원본 텍스트 파일 39개 목록 가져오기
    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
    print(f"🚀 총 {len(txt_files)}개의 텍스트 파일 일괄 청킹을 시작합니다!\n")
    
    total_chunks = 0
    
    # 파일 하나씩 돌면서 작업 수행
    for txt_path in txt_files:
        # 파일명 추출 (예: "imu_ASM330LHH.txt" -> "imu_ASM330LHH")
        base_name = os.path.splitext(os.path.basename(txt_path))[0]
        
        # 앞의 분류명(imu_, gps_ 등)을 떼어내고 순수 부품명만 추출 (예: "ASM330LHH")
        if "_" in base_name:
            component_name = base_name.split("_", 1)[1] 
        else:
            component_name = base_name
            
        # 파일 읽기
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # 청킹 함수 실행!
        chunks = clean_and_chunk_datasheet(text, component_name)
        total_chunks += len(chunks)
        
        # 결과를 새 폴더에 보기 좋게 저장
        out_filename = os.path.join(output_folder, f"{base_name}_chunked.txt")
        with open(out_filename, "w", encoding="utf-8") as out_f:
            for i, chunk in enumerate(chunks):
                out_f.write(f"📦 [Chunk {i+1}]\n")
                out_f.write(chunk)
                out_f.write("\n" + "-"*50 + "\n\n")
                
        print(f"✅ {component_name} -> {len(chunks)}개 조각으로 분할 완료!")
        
    print("-" * 50)
    print(f"🎉 모든 작업 완료! 총 {total_chunks}개의 조각(Chunk)이 '{output_folder}' 폴더에 저장되었습니다.")

if __name__ == "__main__":
    # 코드 저장(Ctrl+S) 후 실행하세요!
    process_all_chunks()