from flask import Flask, render_template, request, flash, redirect, url_for, Response
from utils.plate_recognition import PlateRecognition
from utils.parking_manager import ParkingManager
from utils.gpio_manager import GPIOManager
import threading

app = Flask(__name__)
app.secret_key = "supersecretkey"

# PlateRecognition 및 ParkingManager 초기화
plate_recognizer = PlateRecognition()
parking_manager = ParkingManager()
gpio_manager = GPIOManager()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/entry", methods=["POST"])
def entry():
    """입차 처리"""
    car_number = request.form["car_number"]
    success, message = parking_manager.handle_entry(car_number)
    flash(message, "success" if success else "error")

    if success:
        handle_gpio_on_success(car_number)
    return redirect(url_for("index"))

@app.route("/exit", methods=["POST"])
def exit():
    """출차 처리"""
    car_number = request.form["car_number"]
    success, message = parking_manager.handle_exit(car_number)
    flash(message, "success" if success else "error")

    if success:
        handle_gpio_on_success(car_number)
    return redirect(url_for("index"))

@app.route("/blacklist", methods=["GET", "POST"])
def blacklist():
    """블랙리스트 관리"""
    if request.method == "POST":
        car_number = request.form["car_number"]
        action = request.form["action"]
        success, message = parking_manager.manage_blacklist(car_number, action)
        flash(message, "success" if success else "error")

    # 블랙리스트 조회
    conn = parking_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT car_number FROM blacklist")
    blacklist = cursor.fetchall()
    conn.close()
    return render_template("blacklist.html", blacklist=blacklist)

@app.route("/report", methods=["GET", "POST"])
def report():
    """요금 정책 시뮬레이션"""
    if request.method == "POST":
        new_fee = int(request.form["fee"])
        total_revenue = parking_manager.simulate_revenue(new_fee)
        flash(f"새 요금 정책으로 예상 총 수익은 {total_revenue}원입니다.", "success")
    return render_template("report.html")

@app.route("/stats", methods=["GET", "POST"])
def stats():
    """월별 통계 페이지"""
    if request.method == "POST":
        selected_month = request.form.get("month")
        if not selected_month:
            flash("월을 선택해주세요.", "error")
            # 기본 페이지로 렌더링
            return render_template("stats.html", summary=None, stats_data=None, graph_url=None)

        try:
            # ParkingManager에서 데이터 가져오기
            summary, stats_data = parking_manager.get_monthly_stats(selected_month)
            graph_path = parking_manager.generate_monthly_graph(stats_data, selected_month)
            graph_url = url_for("static", filename="graph.png") if graph_path else None

            return render_template("stats.html", summary=summary, stats_data=stats_data, graph_url=graph_url)

        except Exception as e:
            flash(f"통계 생성 중 오류가 발생했습니다: {str(e)}", "error")
            return render_template("stats.html", summary=None, stats_data=None, graph_url=None)

    # GET 요청: 기본 템플릿 렌더링
    return render_template("stats.html", summary=None, stats_data=None, graph_url=None)


@app.route("/video_feed")
def video_feed():
    """카메라 실시간 스트리밍"""
    return Response(plate_recognizer.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
def capture():
    """카메라 프레임 캡처 및 번호판 인식"""
    gpio_manager.turn_on_blue()  # 파란색 LED 켜기 (인식 중)
    plates = plate_recognizer.capture_plate()  # 번호판 인식
    gpio_manager.turn_off_blue()  # 파란색 LED 끄기 (인식 완료)
    if plates:
        car_number = plates[0]
        action = request.form.get("action")
        if action == "entry":
            success, message = parking_manager.handle_entry(car_number)
        elif action == "exit":
            success, message = parking_manager.handle_exit(car_number)
        else:
            return {"status": "error", "message": "알 수 없는 동작"}

        if success:
            handle_gpio_on_success(car_number)
        return {"status": "success", "message": message}
    return {"status": "error", "message": "번호판을 감지하지 못했습니다."}

@app.route("/current_parking", methods=["GET"])
def current_parking():
    """현재 주차된 차량 정보 조회 + 남은 자리"""
    available_spots = parking_manager.max_spots - parking_manager.get_occupied_spots()
    car_info = parking_manager.get_current_parking_info()
    return render_template("current_parking.html", car_info=car_info, available_spots=available_spots)

@app.route("/shutdown_gpio")
def shutdown_gpio():
    """GPIO 리소스 정리"""
    gpio_manager.cleanup()
    return "GPIO cleaned up", 200

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        gpio_manager.cleanup()  # 프로그램 종료 시 GPIO 정리

def handle_gpio_on_success(car_number):
    threading.Thread(target=gpio_manager.blink_red, kwargs={"duration": 7}).start()
    threading.Thread(target=gpio_manager.run_fnd_and_servo, args=(car_number[-4:],)).start()
    threading.Thread(target=gpio_manager.play_buzzer, kwargs={"duration": 7}).start()

