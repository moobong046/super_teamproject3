# 차량용 블랙박스 인텔리전스 Q&A 시스템 (Hybrid RAG)

차량용 블랙박스 및 전장 부품 데이터시트(비정형)와 BOM/단가표(정형)를 통합 분석하여, FAE(Field Application Engineer) 수준의 전문적인 답변을 제공하는 **하이브리드 RAG 및 오토노머스 에이전트 시스템**입니다.

## 📌 프로젝트 개요
* **도입 배경:** 수많은 부품 라인업을 보유한 ODM 환경에서, 기존 FAE가 방대한 데이터시트와 BOM을 수작업으로 대조하며 답변하던 병목 현상과 휴먼 에러를 해결하기 위함.
* **핵심 목표:** 환각(Hallucination) 현상을 원천 차단한 100% 팩트 기반의 부품 스펙 비교 및 단가 계산 자동화 파이프라인 구축.

## ⚙️ 시스템 아키텍처 및 파이프라인
본 프로젝트는 **정형(SQL) + 비정형(Vector DB) 데이터 투트랙 처리**와 이를 조율하는 **LLM 에이전트**로 구성되어 있습니다.

1. **정형 데이터 파이프라인 (SQL)**
   * `SQLite`를 활용하여 BOM 구성표 및 부품 제조사/단가 테이블 구축.
   * 인메모리 조인(Join) 캐싱을 통해 즉각적인 단가 연산 및 팩트 필터링 수행.
2. **비정형 데이터 파이프라인 (Vector DB)**
   * `PyMuPDF` 기반 데이터시트 파싱 및 `ChromaDB` 임베딩.
   * 메타데이터 통합 관리 및 로컬 영구 저장(Persistent) 최적화.
3. **LLM 및 에이전트 (Agent Orchestration)**
   * `GPT-4o-mini`의 Function Calling을 활용하여 3가지 핵심 도구(필터링, 단가 계산, 시맨틱 검색)를 자율적으로 판단하고 호출.

## 🧪 핵심 엔지니어링 
**검색 품질 최적화를 위한 2-Step Grid Search**
RAG 시스템의 성능을 극대화하기 위해 임베딩 모델과 Chunk Size 조합을 교차 검증했습니다.
* **Qwen3-Embedding-0.6B (Chunk 800):** 넓은 문맥 유지력과 안정적인 팩트 전달.
* **BAAI/bge-m3 (Chunk 500):** 압도적인 검색 깊이(Recall)와 부품 카운팅 등 혁신적인 통계 구조화 능력 발휘.
* **최종 채택:** 실제 산업 응용 분야(ADAS 등)까지 통찰을 제공하고 분석 역량이 뛰어난 **BGE-M3 (Chunk 500 / Overlap 100)** 환경 최종 적용.

## 📂 디렉토리 구조 (Directory Structure)
```text
📦 super_teamproject3
 ┣ 📂 api/               # Gradio 웹 UI 및 서버 실행을 위한 최종 통합 코드
 ┣ 📂 data/              # 원본 및 가공 데이터 저장소
 ┃ ┣ 📂 datasheet/       # 원본 PDF 규격서 및 이미지
 ┃ ┣ 📂 parsed_texts/    # 파싱된 텍스트 데이터
 ┃ ┣ 📂 chunked_texts/   # 임베딩을 위해 분할된 청크 데이터
 ┃ ┗ 📂 sql/             # BOM/단가 CSV 원본 및 SQLite DB 변환 로직, dashcam_rag2.db
 ┣ 📂 notebooks/         # 기능별 단위 테스트 (SQL 쿼리, 청킹 품질, Vector DB 검색 테스트)
 ┣ 📂 src/               # 데이터 파이프라인 구성을 위한 핵심 모듈 및 스크립트
 ┣ 📜 README.md          # 프로젝트 상세 소개서
 ┣ 📜 requirements.txt   # 의존성 패키지 목록
 ┗ 📜 LICENSE            # MIT 라이선스
