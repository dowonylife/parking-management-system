import sqlite3
import datetime
import os
import matplotlib.pyplot as plt

class ParkingManager:
    def __init__(self, db_path="parking.db", max_spots=100):
        self.db_path = db_path
        self.max_spots = max_spots
        self.initialize_db()

    def initialize_db(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_lot (
                car_number TEXT PRIMARY KEY,
                entry_time TEXT,
                exit_time TEXT,
                fee INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                car_number TEXT PRIMARY KEY
            )
        """)
        conn.commit()
        conn.close()

    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)

    def get_occupied_spots(self):
        """현재 주차된 차량 수 반환"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM parking_lot WHERE exit_time IS NULL")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def handle_entry(self, car_number):
        """입차 처리"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 이미 입차된 차량인지 확인
        cursor.execute("SELECT * FROM parking_lot WHERE car_number = ? AND exit_time IS NULL", (car_number,))
        if cursor.fetchone():
            conn.close()
            return False, f"차량 {car_number}은 이미 입차된 상태입니다."

        # 블랙리스트 확인
        if self.is_blacklisted(car_number):
            return False, f"차량 {car_number}은 블랙리스트에 등록되어 있습니다."

        # 주차 공간 확인
        if self.get_occupied_spots() >= self.max_spots:
            conn.close()
            return False, "주차 공간이 가득 찼습니다."

        # 입차 기록 추가
        entry_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute("SELECT * FROM parking_lot WHERE car_number = ? AND exit_time IS NULL", (car_number,))
            if cursor.fetchone():
                conn.close()
                return False, f"차량 {car_number}은 이미 입차된 상태입니다."

            cursor.execute("INSERT INTO parking_lot (car_number, entry_time, exit_time, fee) VALUES (?, ?, NULL, NULL)",
                        (car_number, entry_time))
            conn.commit()
            return True, f"차량 {car_number} 입차 완료."
        except sqlite3.IntegrityError:
            return False, "입차 처리 중 오류가 발생했습니다."
        finally:
            conn.close()


    def handle_exit(self, car_number):
        """출차 처리"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 입차 기록 확인
        cursor.execute("SELECT entry_time FROM parking_lot WHERE car_number = ? AND exit_time IS NULL", (car_number,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False, "입차 기록이 없습니다."
        
        # 블랙리스트 확인
        if self.is_blacklisted(car_number):
            return False, f"차량 {car_number}은 블랙리스트에 등록되어 있습니다."

        # 출차 기록 및 요금 계산
        entry_time = datetime.datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        exit_time = datetime.datetime.now()
        duration = exit_time - entry_time
        fee = max(1, int(duration.total_seconds() / 3600)) * 1000

        cursor.execute("UPDATE parking_lot SET exit_time = ?, fee = ? WHERE car_number = ?",
                       (exit_time.strftime("%Y-%m-%d %H:%M:%S"), fee, car_number))
        conn.commit()
        conn.close()
        return True, f"차량 {car_number} 출차 완료. 요금: {fee}원"

    def manage_blacklist(self, car_number, action):
        """블랙리스트 추가/제거"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if action == "add":
            cursor.execute("INSERT OR IGNORE INTO blacklist (car_number) VALUES (?)", (car_number,))
            message = f"차량 {car_number}이 블랙리스트에 추가되었습니다."
        elif action == "remove":
            cursor.execute("DELETE FROM blacklist WHERE car_number = ?", (car_number,))
            message = f"차량 {car_number}이 블랙리스트에서 제거되었습니다."
        else:
            conn.close()
            return False, "알 수 없는 작업입니다."

        conn.commit()
        conn.close()
        return True, message

    def simulate_revenue(self, fee_per_hour):
        """새 요금 정책으로 예상 수익 계산"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT entry_time, exit_time FROM parking_lot WHERE exit_time IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()

        total_revenue = 0
        for entry_time, exit_time in rows:
            entry_time = datetime.datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
            exit_time = datetime.datetime.strptime(exit_time, "%Y-%m-%d %H:%M:%S")
            duration = exit_time - entry_time
            total_revenue += max(1, int(duration.total_seconds() / 3600)) * fee_per_hour
        return total_revenue

    def generate_monthly_stats(self, selected_month):
        """월별 통계 데이터와 그래프 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT strftime('%d', exit_time) AS day, COUNT(*) AS count, SUM(fee) AS total_fee
            FROM parking_lot
            WHERE strftime('%Y-%m', exit_time) = ?
            GROUP BY day
        """, (selected_month,))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return [], None

        # 데이터 분리
        days = [row[0] for row in results]
        counts = [row[1] for row in results]
        total_fees = [row[2] for row in results]

        # 그래프 생성
        graph_path = os.path.join("static", "graph.png")
        plt.bar(days, counts, label="출차 수")
        plt.plot(days, total_fees, label="정산 금액", color="red", marker="o")
        plt.xlabel("일")
        plt.ylabel("출차 수 및 금액")
        plt.title(f"{selected_month} 통계")
        plt.legend()
        plt.savefig(graph_path)
        plt.close()
        return results, graph_path
    
    def get_current_parking_info(self):
        """현재 주차된 차량 정보와 예상 비용 계산"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 현재 주차된 차량 조회
        cursor.execute("""
            SELECT car_number, entry_time 
            FROM parking_lot 
            WHERE exit_time IS NULL
        """)
        parked_cars = cursor.fetchall()  # [(차량 번호, 입차 시간), ...]

        conn.close()

        # 예상 비용 계산
        current_time = datetime.datetime.now()
        car_info = []
        for car_number, entry_time in parked_cars:
            entry_time_dt = datetime.datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
            duration = current_time - entry_time_dt
            hours = int(duration.total_seconds() // 3600) + 1  # 최소 1시간
            estimated_cost = hours * 1000  # 시간당 1000원
            car_info.append({
                "car_number": car_number,
                "entry_time": entry_time,
                "hours": hours,
                "estimated_cost": estimated_cost
            })
        return car_info
    
    def get_monthly_stats(self, month):
        """월별 통계 데이터 및 요약 정보 반환"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 요약 정보 조회
            cursor.execute("""
                SELECT COUNT(*) AS car_count, SUM(fee) AS total_revenue
                FROM parking_lot
                WHERE strftime('%Y-%m', exit_time) = ?
            """, (month,))
            summary_row = cursor.fetchone()
            summary = {
                "month": month,
                "total_cars": summary_row[0] or 0,
                "total_revenue": summary_row[1] or 0
            }

            # 일별 데이터 조회
            cursor.execute("""
                SELECT strftime('%d', exit_time) AS day, COUNT(*) AS car_count, SUM(fee) AS revenue
                FROM parking_lot
                WHERE strftime('%Y-%m', exit_time) = ?
                GROUP BY day
            """, (month,))
            stats_rows = cursor.fetchall()
            stats_data = {row[0]: {"car_count": row[1], "revenue": row[2]} for row in stats_rows}

        finally:
            conn.close()
        return summary, stats_data

    def generate_monthly_graph(self, stats_data, month):
        """월별 통계를 그래프로 생성"""
        if not stats_data:
            return None

        days = [int(day) for day in stats_data.keys()]
        car_counts = [data["car_count"] for data in stats_data.values()]
        revenues = [data["revenue"] for data in stats_data.values()]

        # 그래프 생성
        plt.figure(figsize=(10, 5))
        plt.bar(days, car_counts, label="차량 수", alpha=0.7)
        plt.plot(days, revenues, label="수익 (원)", color="red", marker="o")
        plt.title(f"{month} 월별 통계")
        plt.xlabel("날짜")
        plt.ylabel("차량 수 / 수익 (원)")
        plt.legend()
        graph_path = "static/graph.png"
        plt.savefig(graph_path)
        plt.close()
        return graph_path

    def is_blacklisted(self, car_number):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blacklist WHERE car_number = ?", (car_number,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

        
    
