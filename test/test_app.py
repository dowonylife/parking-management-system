from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import datetime
import matplotlib.pyplot as plt
from matplotlib import rc
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # 플래시 메시지에 필요

# 사용자 지정 폰트 설정
rc('font', family='NanumGothic')

# 데이터베이스 경로 및 초기화
DB_PATH = "parking.db"
MAX_PARKING_SPOTS = 10  # 최대 주차 공간 설정

def initialize_db():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 주차 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_lot (
            car_number TEXT PRIMARY KEY,
            entry_time TEXT,
            exit_time TEXT,
            fee INTEGER
        )
    """)

    # 블랙리스트 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            car_number TEXT PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()

# 정적 파일 디렉토리 확인 및 생성
if not os.path.exists("static"):
    os.makedirs("static")

def get_occupied_spots():
    """현재 주차된 차량 수 반환"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM parking_lot WHERE exit_time IS NULL")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def is_blacklisted(car_number):
    """차량이 블랙리스트에 있는지 확인"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blacklist WHERE car_number = ?", (car_number,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

@app.route("/")
def index():
    """메인 페이지"""
    available_spots = MAX_PARKING_SPOTS - get_occupied_spots()
    return render_template("index.html", available_spots=available_spots)

@app.route("/entry", methods=["POST"])
def entry():
    """입차 처리"""
    car_number = request.form["car_number"]
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 블랙리스트 확인
        if is_blacklisted(car_number):
            flash(f"차량 {car_number}은 블랙리스트에 등록되어 입차할 수 없습니다.", "error")
            return redirect(url_for("index"))

        # 주차 공간 확인
        if get_occupied_spots() >= MAX_PARKING_SPOTS:
            flash("주차 공간이 가득 찼습니다!", "error")
            return redirect(url_for("index"))

        # 중복 확인
        cursor.execute("SELECT * FROM parking_lot WHERE car_number = ? AND exit_time IS NULL", (car_number,))
        if cursor.fetchone():
            flash("이미 입차된 차량입니다.", "error")
            return redirect(url_for("index"))

        # 입차 기록 추가
        entry_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO parking_lot (car_number, entry_time, exit_time, fee) VALUES (?, ?, NULL, NULL)",
                       (car_number, entry_time))
        conn.commit()
        flash(f"차량 {car_number} 입차 처리 완료.", "success")
    except Exception as e:
        flash(f"입차 처리 중 오류가 발생했습니다: {str(e)}", "error")
    finally:
        conn.close()
    return redirect(url_for("index"))

@app.route("/exit", methods=["POST"])
def exit():
    """출차 처리"""
    car_number = request.form["car_number"]
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 입차 기록 확인
        cursor.execute("SELECT entry_time FROM parking_lot WHERE car_number = ? AND exit_time IS NULL", (car_number,))
        result = cursor.fetchone()
        if not result:
            flash("입차 기록이 없습니다.", "error")
            return redirect(url_for("index"))

        # 출차 기록 및 요금 계산
        entry_time = datetime.datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        exit_time = datetime.datetime.now()
        duration = exit_time - entry_time
        hours = duration.total_seconds() / 3600
        fee = max(1, int(hours)) * 1000

        cursor.execute("UPDATE parking_lot SET exit_time = ?, fee = ? WHERE car_number = ?",
                       (exit_time.strftime("%Y-%m-%d %H:%M:%S"), fee, car_number))
        conn.commit()
        flash(f"차량 {car_number} 출차 완료. 요금: {fee}원", "success")
    except Exception as e:
        flash(f"출차 처리 중 오류가 발생했습니다: {str(e)}", "error")
    finally:
        conn.close()
    return redirect(url_for("index"))

@app.route("/blacklist", methods=["GET", "POST"])
def blacklist():
    """블랙리스트 관리"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == "POST":
        car_number = request.form["car_number"]
        action = request.form["action"]

        if action == "add":
            cursor.execute("INSERT OR IGNORE INTO blacklist (car_number) VALUES (?)", (car_number,))
            flash(f"차량 {car_number}이 블랙리스트에 추가되었습니다.", "success")
        elif action == "remove":
            cursor.execute("DELETE FROM blacklist WHERE car_number = ?", (car_number,))
            flash(f"차량 {car_number}이 블랙리스트에서 제거되었습니다.", "success")

        conn.commit()

    # 블랙리스트 조회
    cursor.execute("SELECT car_number FROM blacklist")
    blacklist = cursor.fetchall()
    conn.close()
    return render_template("blacklist.html", blacklist=blacklist)

@app.route("/report", methods=["GET", "POST"])
def report():
    """요금 정책 시뮬레이션"""
    if request.method == "POST":
        new_fee = int(request.form["fee"])
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 현재 데이터 기반 예상 수익 계산
        cursor.execute("SELECT entry_time, exit_time FROM parking_lot WHERE exit_time IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()

        total_revenue = 0
        for entry_time, exit_time in rows:
            entry_time = datetime.datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
            exit_time = datetime.datetime.strptime(exit_time, "%Y-%m-%d %H:%M:%S")
            duration = exit_time - entry_time
            hours = duration.total_seconds() / 3600
            total_revenue += max(1, int(hours)) * new_fee

        flash(f"새 요금 정책으로 예상 총 수익은 {total_revenue}원입니다.", "success")
    return render_template("report.html")

@app.route("/stats", methods=["GET", "POST"])
def stats():
    """월별 통계 페이지"""
    if request.method == "POST":
        selected_month = request.form.get("month")
        if not selected_month:
            flash("월을 선택해주세요.", "error")
            return redirect(url_for("stats"))

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # 데이터 가져오기
            cursor.execute("""
                SELECT strftime('%d', exit_time) AS day, COUNT(*) AS count, SUM(fee) AS total_fee
                FROM parking_lot
                WHERE strftime('%Y-%m', exit_time) = ?
                GROUP BY day
            """, (selected_month,))
            results = cursor.fetchall()
            conn.close()

            if not results:
                flash(f"{selected_month}에 출차된 기록이 없습니다.", "info")
                return render_template("stats.html", graph_url=None)

            # 데이터 분리
            days = [row[0] for row in results]
            counts = [row[1] for row in results]
            total_fees = [row[2] for row in results]

            # 그래프 생성
            plt.bar(days, counts, label="출차 수")
            plt.plot(days, total_fees, label="정산 금액", color="red", marker="o")
            plt.xlabel("일")
            plt.ylabel("출차 수 및 금액")
            plt.title(f"{selected_month} 통계")
            plt.legend()
            plt.savefig("static/graph.png")
            plt.close()

            return render_template("stats.html", graph_url="static/graph.png")

        except Exception as e:
            flash(f"통계 생성 중 오류가 발생했습니다: {str(e)}", "error")
            return render_template("stats.html", graph_url=None)

    return render_template("stats.html", graph_url=None)

if __name__ == "__main__":
    initialize_db()
    app.run(debug=True)
