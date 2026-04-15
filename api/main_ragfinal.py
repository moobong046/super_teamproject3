import sys
import os
import json
import sqlite3
import chromadb
import numpy as np
import gradio as gr
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI

# ==========================================
# [1] 환경 설정 및 초기화
# ==========================================
load_dotenv()
os.environ["PYTHONUTF8"] = "1"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("🔍 시스템 초기화 중 (Qwen Embedding & SQLite)...")
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={'normalize_embeddings': True}
)

chroma_client = chromadb.PersistentClient(path="./chroma_db_bge_500")
collections = chroma_client.list_collections()
collection = chroma_client.get_collection(name=collections[0].name) if collections else None

sqlite_conn = sqlite3.connect('dashcam_rag2.db', check_same_thread=False)
cursor = sqlite_conn.cursor()

# ==========================================
# [2] 고도화된 데이터 로딩 (제조사-부품-모델 매핑)
# ==========================================
def db_get_all_models_info():
    # 1. 부품 정보 로드 (제조사 포함)
    cursor.execute("SELECT component_name, manufacturer, category, tier, estimated_price_usd FROM component_info_with_manufacturer")
    comp_info = {}
    for row in cursor.fetchall():
        if row[0]:
            comp_info[str(row[0]).strip().lower()] = {
                "part_name": row[0],
                "manufacturer": row[1],
                "category": row[2], 
                "tier": row[3], 
                "price": row[4]
            }
    
    # 2. 모델 BOM 정보 로드
    cursor.execute("SELECT * FROM bom_table")
    rows = cursor.fetchall()
    col_names = [d[0] for d in cursor.description]
    
    all_models = []
    for row in rows:
        bom_dict = dict(zip(col_names, row))
        model_info = {
            "model_name": bom_dict.get("model_name"), 
            "brand": bom_dict.get("brand"), 
            "components": {},
            "total_price_usd": 0
        }
        
        # 각 카테고리별 부품 매칭
        for cat in ['image_sensor', 'processor', 'memory', 'imu', 'gps', 'wifi_module', 'power', 'rtc']:
            p_name = bom_dict.get(cat)
            if p_name:
                key = str(p_name).strip().lower()
                if key in comp_info:
                    spec = comp_info[key]
                    model_info["components"][cat] = spec
                    model_info["total_price_usd"] += spec["price"] if spec["price"] else 0
        all_models.append(model_info)
    return all_models

# ==========================================
# [3] 질문 해결을 위한 전용 도구(Tools)
# ==========================================

def tool_filter_models_advanced(brand=None, component_manufacturer=None, category=None):
    """
    브랜드(FineVu 등)와 부품 제조사(Samsung 등)를 구분하여 필터링합니다.
    """
    all_data = db_get_all_models_info()
    filtered = []
    
    for m in all_data:
        # 브랜드 필터 (블랙박스 제조사)
        if brand and str(brand).lower() not in str(m["brand"]).lower():
            continue
            
        # 부품 제조사 필터 (부품을 만든 회사)
        if component_manufacturer:
            manuf_match = False
            for cat, spec in m["components"].items():
                if str(component_manufacturer).lower() in str(spec["manufacturer"]).lower():
                    # 카테고리 조건이 있다면 그것까지 확인
                    if category and str(category).lower() != str(cat).lower():
                        continue
                    manuf_match = True
                    break
            if not manuf_match: continue
            
        filtered.append(m)
    return json.dumps(filtered, ensure_ascii=False)

def tool_get_component_avg_price(manufacturer=None, category=None):
    """
    특정 제조사나 카테고리의 부품 단가 평균을 계산합니다.
    """
    query = "SELECT estimated_price_usd FROM component_info_with_manufacturer WHERE estimated_price_usd IS NOT NULL"
    params = []
    if manufacturer:
        query += " AND manufacturer LIKE ?"
        params.append(f"%{manufacturer}%")
    if category:
        query += " AND category = ?"
        params.append(category)
        
    cursor.execute(query, params)
    prices = [r[0] for r in cursor.fetchall()]
    
    if not prices: return json.dumps({"count": 0, "avg": 0})
    return json.dumps({"count": len(prices), "avg": round(np.mean(prices), 2)}, ensure_ascii=False)

def tool_search_vdb(keyword):
    if not collection: return "VDB not initialized."
    query_vector = embedding_model.embed_query(keyword)
    res = collection.query(query_embeddings=[query_vector], n_results=3)
    return json.dumps(res['documents'][0], ensure_ascii=False)

# ==========================================
# [4] 에이전트 실행 로직
# ==========================================

agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "tool_filter_models_advanced",
            "description": "블랙박스 브랜드명 또는 부품 제조사(칩셋 제조사) 명칭으로 모델을 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "brand": {"type": "string", "description": "블랙박스 브랜드 (예: FineVu, Inavi)"},
                    "component_manufacturer": {"type": "string", "description": "부품 제조사 (예: Samsung, STMicroelectronics, TI)"},
                    "category": {"type": "string", "description": "부품 종류 (예: memory, imu, power)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_get_component_avg_price",
            "description": "특정 제조사나 카테고리 부품의 평균 단가를 계산합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "manufacturer": {"type": "string", "description": "부품 제조사 (예: Texas Instruments)"},
                    "category": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_search_vdb",
            "description": "부품의 상세 스펙이나 칩셋 정보를 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {"keyword": {"type": "string"}}
            }
        }
    }
]

def smart_hybrid_answer(user_question):
    system_prompt = """
    당신은 차량용 블랙박스 분야의 10년 차 시니어 FAE(Field Application Engineer)입니다.
    도구(Tools)가 반환한 JSON 데이터에만 근거하여 전문적이고 구조화된 답변을 제공하세요.
    [1. 핵심 답변 원칙: Concise & Focused]
    - 질문의 본질에 집중: 모델 리스트를 물었다면 전체 BOM을 나열하지 말고 해당 모델명 위주로 답변하세요.
    - 데이터 연결 및 구분: 'FineVu(브랜드)'와 'Samsung(부품 제조사)'을 명확히 구분하고, 'TI' 등 제조사 언급 시 관련 도구를 사용하여 정확한 부품 정보를 먼저 확보하세요.
    - 할루시네이션 방지: 데이터가 없으면 "현재 DB 내에 관련 정보가 확인되지 않습니다"라고 명확히 안내하세요.
    [2. 가독성 및 구조화 규칙]
    - 표(Table) 활용: 비교 대상이 2개 이상일 경우 마크다운 표를 사용하되, 질문과 관련 없는 컬럼은 과감히 생략하세요.
    - 강조 처리: 핵심 모델명, 부품명, 제조사는 **볼드체**로, 가격은 '$' 기호를 포함하여 표기하세요.
    - 정보 그룹화: 리스트가 많을 경우 제조사별/티어별로 그룹화하여 가독성을 높이세요.
    [3. 엔지니어의 심층 분석]
    - 단순 나열 지양: 각 모델의 주요 특징을 간략히 설명하여 전문성을 더하세요.
    - Insight 섹션: 답변 하단에 해당 부품 조합의 기술적 특징이나 시장 내 위치에 대한 엔지니어로서의 짧은 코멘트를 추가하세요.
    """
    
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_question}]
    
    for _ in range(5):
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=agent_tools, temperature=0)
        msg = response.choices[0].message
        if not msg.tool_calls: return msg.content
        
        messages.append(msg)
        for tool in msg.tool_calls:
            args = json.loads(tool.function.arguments)
            if tool.function.name == "tool_filter_models_advanced":
                res = tool_filter_models_advanced(**args)
            elif tool.function.name == "tool_get_component_avg_price":
                res = tool_get_component_avg_price(**args)
            elif tool.function.name == "tool_search_vdb":
                res = tool_search_vdb(args.get("keyword"))
            messages.append({"tool_call_id": tool.id, "role": "tool", "name": tool.function.name, "content": res})

    return client.chat.completions.create(model="gpt-4o-mini", messages=messages).choices[0].message.content

demo = gr.ChatInterface(
    fn=lambda msg, hist: smart_hybrid_answer(msg),
    title="차량용 블랙박스 부품 스펙 Q&A 시스템",
    description="부품 스펙 정보를 자동으로 응답할 수 있는 AI 시스템",
    examples=[
        "QXD8000과 LXQ3000의 GPS 부품을 비교해 주고, 가격 차이뿐만 아니라 두 부품의 실제 기술 스펙(수신 채널, 지원 위성 등)을 검색해서 왜 가격 차이가 나는지 엔지니어 관점에서 설명해주세요.",
        "Ambarella 프로세서중에 가장 비싼 부품을 사용하는 블랙박스 모델은 무엇인가요?",
        "현재 데이터셋에서 high티어 부품을 가장 많이 사용한 브랜드는 어디인가요?",
        "IMX678 센서와 주로 결합되는 High 티어 프로세서(예: CV5)의 스펙을 검색해서, 이 프로세서가 고해상도 영상 처리에 적합한 이유를 알려주세요."
    ]
)

if __name__ == "__main__":
    print("🚀 Gradio 서버를 시작합니다...")
    demo.launch(server_name="0.0.0.0", server_port=7860)