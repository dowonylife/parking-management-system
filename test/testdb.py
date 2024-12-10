import sqlite3
import datetime
import random

DB_PATH = "parking.db"

# 데이터베이스 초기화
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_lot (
            car_number TEXT PRIMARY KEY,
            entry_time TEXT,
            exit_time TEXT,
            fee INTEGER
        )
    """)
    conn.commit()
    conn.close()

# 샘플 데이터 생성
def populate_sample_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 기존 데이터 삭제
    cursor.execute("DELETE FROM parking_lot")
    conn.commit()

    # 차량 번호 샘플
    car_numbers = [f"{random.randint(1000, 9999)}-{random.choice(['AB', 'CD', 'EF'])}" for _ in range(20)]

    # 현재 월
    now = datetime.datetime.now()
    current_month = now.strftime("%Y-%m")

    # 샘플 데이터 삽입
    for car_number in car_numbers:
        # 입차 시간: 해당 월 내 랜덤한 날짜와 시간
        entry_date = random.randint(1, 28)
        entry_time = datetime.datetime.strptime(f"{current_month}-{entry_date} {random.randint(6, 20)}:{random.randint(0, 59)}:00", "%Y-%m-%d %H:%M:%S")

        # 출차 시간: 입차 시간 이후 1~6시간
        exit_time = entry_time + datetime.timedelta(hours=random.randint(1, 6))

        # 요금 계산 (시간당 1000원, 최소 1시간)
        hours_parked = (exit_time - entry_time).seconds / 3600
        fee = max(1, int(hours_parked)) * 1000

        # 데이터 삽입
        cursor.execute("""
            INSERT INTO parking_lot (car_number, entry_time, exit_time, fee)
            VALUES (?, ?, ?, ?)
        """, (car_number, entry_time.strftime("%Y-%m-%d %H:%M:%S"), exit_time.strftime("%Y-%m-%d %H:%M:%S"), fee))

    conn.commit()
    conn.close()
    print("샘플 데이터가 성공적으로 추가되었습니다.")

# 메인 실행
if __name__ == "__main__":
    initialize_db()
    populate_sample_data()
