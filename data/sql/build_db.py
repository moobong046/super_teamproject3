import pandas as pd
import sqlite3

def create_database():
    print("🚀 데이터베이스 구축을 시작합니다...")

    # 1. 두 개의 CSV 파일 읽어오기
    print("1️⃣ CSV 파일을 읽는 중...")
    df_bom = pd.read_csv('bom_data.csv')
    df_info = pd.read_csv('component_info_with_manufacturer.csv')

    # 2. SQLite 데이터베이스 생성 및 연결
    # (폴더에 dashcam_rag.db 파일이 없으면 자동으로 새로 만듭니다)
    print("2️⃣ SQLite 데이터베이스에 연결합니다...")
    conn = sqlite3.connect('dashcam_rag.db')

    # 3. 데이터프레임을 SQL 테이블로 변환하여 굽기
    # if_exists='replace' : 코드를 다시 실행해도 에러 없이 기존 테이블을 덮어씌웁니다.
    print("3️⃣ 데이터를 SQL 테이블로 굽는 중...")
    df_bom.to_sql('bom_table', conn, if_exists='replace', index=False)
    df_info.to_sql('component_info', conn, if_exists='replace', index=False)

    # 4. 작업 완료 후 연결 종료
    conn.close()
    print("✅ 성공! 'dashcam_rag2.db' 파일에 두 개의 테이블이 완벽하게 저장되었습니다!")

if __name__ == "__main__":
    create_database()