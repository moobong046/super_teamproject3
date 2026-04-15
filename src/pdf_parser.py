import fitz  # PyMuPDF
import os
import glob  # 폴더 내의 파일 목록을 한 번에 불러오는 마법의 도구

def parse_all_datasheets():
    input_folder = "datasheet"
    text_out_folder = "parsed_texts"      # 39개의 텍스트 파일이 모일 새 폴더
    img_out_folder = "extracted_images"   # 이미지들이 모일 폴더
    
    # 텍스트와 이미지를 저장할 큰 폴더부터 만듭니다.
    os.makedirs(text_out_folder, exist_ok=True)
    os.makedirs(img_out_folder, exist_ok=True)

    # datasheet 폴더 안의 모든 .pdf 파일을 리스트로 가져옵니다!
    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))
    print(f"🚀 총 {len(pdf_files)}개의 PDF 파일을 찾았습니다! 일괄 파싱을 시작합니다...\n")

    # 39번(파일 개수만큼) 자동으로 돕니다.
    for pdf_path in pdf_files:
        # 파일 경로에서 순수하게 이름만 쏙 뽑아냅니다. (예: datasheet\gps_L76-L.pdf -> gps_L76-L)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"🔄 변환 중: {base_name}")
        
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"❌ {base_name} 파일 열기 실패: {e}")
            continue

        # 이 PDF만의 전용 텍스트 파일을 만듭니다. (예: parsed_texts/gps_L76-L.txt)
        txt_filename = os.path.join(text_out_folder, f"{base_name}.txt")
        
        with open(txt_filename, "w", encoding="utf-8") as f_txt:
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # 1. 텍스트 추출
                text = page.get_text()
                f_txt.write(f"\n================ [Page {page_num + 1}] ================\n")
                f_txt.write(text)
                f_txt.write("\n")
                
                # 2. 이미지 추출
                images = page.get_images(full=True)
                if images:
                    # 이미지가 너무 많아 섞일 수 있으니, 부품 이름으로 하위 폴더를 만들어 깔끔하게 정리합니다.
                    part_img_folder = os.path.join(img_out_folder, base_name)
                    os.makedirs(part_img_folder, exist_ok=True)
                    
                    for img_index, img in enumerate(images):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        image_filename = os.path.join(part_img_folder, f"page{page_num+1}_img{img_index}.{image_ext}")
                        with open(image_filename, "wb") as f_img:
                            f_img.write(image_bytes)
                            
        doc.close()

    print("\n✅ 39개 파일 자동 파싱이 완벽하게 끝났습니다! 'parsed_texts' 폴더를 확인해보세요.")

if __name__ == "__main__":
    # 이제 파일 이름을 일일이 적어줄 필요 없이 이 함수 하나면 끝납니다.
    # 꼭 Ctrl + S 로 저장하고 실행하세요!
    parse_all_datasheets()