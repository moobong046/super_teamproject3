import sqlite3
import pandas as pd

# 1. 데이터베이스 연결
conn = sqlite3.connect('dashcam_rag.db')

# 2. SQL 쿼리 작성 (JOIN 사용)
# bom_table(B)의 이미지 센서와 component_info(C)의 부품명을 조인하여 가격을 가져옵니다.
query = """
    SELECT 
        B.brand, 
        B.model_name, 
        B.image_sensor, 
        C.estimated_price_usd AS sensor_price
    FROM bom_table B
    JOIN component_info C 
      ON B.image_sensor = C.component_name
    WHERE C.estimated_price_usd > 10.0
"""

# 3. 쿼리 실행 및 결과를 데이터프레임으로 예쁘게 받아오기
df_result = pd.read_sql_query(query, conn)

print("🔍 조인(JOIN)된 쿼리 결과 확인:")
print(df_result.head(10)) # 결과 중 위에서 10개만 출력

# 4. 연결 종료
conn.close()