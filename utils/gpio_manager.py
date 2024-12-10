import RPi.GPIO as GPIO
import time
import threading

class GPIOManager:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # RGB LED 핀 설정 (BCM 모드)
        self.RED = 6
        self.GREEN = 19
        self.BLUE = 26
        GPIO.setup(self.RED, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.GREEN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.BLUE, GPIO.OUT, initial=GPIO.LOW)

        # 부저 핀 설정
        self.BUZZER_PIN = 16
        GPIO.setup(self.BUZZER_PIN, GPIO.OUT)
        self.buzzer_pwm = GPIO.PWM(self.BUZZER_PIN, 440)  # 440Hz 기본 주파수

        # FND 초기화
        self.segments = (11, 4, 23, 8, 7, 10, 13, 25)
        for segment in self.segments:
            GPIO.setup(segment, GPIO.OUT)
            GPIO.output(segment, 0)

        self.digits = (22, 27, 17, 24)
        for digit in self.digits:
            GPIO.setup(digit, GPIO.OUT)
            GPIO.output(digit, 1)

        self.num = {
            ' ': (0, 0, 0, 0, 0, 0, 0),
            '0': (1, 1, 1, 1, 1, 1, 0),
            '1': (0, 1, 1, 0, 0, 0, 0),
            '2': (1, 1, 0, 1, 1, 0, 1),
            '3': (1, 1, 1, 1, 0, 0, 1),
            '4': (0, 1, 1, 0, 0, 1, 1),
            '5': (1, 0, 1, 1, 0, 1, 1),
            '6': (1, 0, 1, 1, 1, 1, 1),
            '7': (1, 1, 1, 0, 0, 0, 0),
            '8': (1, 1, 1, 1, 1, 1, 1),
            '9': (1, 1, 1, 1, 0, 1, 1)
        }

        # 서보모터 초기화
        self.servo_pin = 18
        GPIO.setup(self.servo_pin, GPIO.OUT)
        self.servo = GPIO.PWM(self.servo_pin, 50)  # 50Hz
        self.servo.start(0)

        self.SERVO_MAX_DUTY = 12
        self.SERVO_MIN_DUTY = 3

    def play_buzzer(self, duration=7):
        """부저를 설정된 시간 동안 동작"""
        end_time = time.time() + duration
        while time.time() < end_time:
            self.buzzer_pwm.start(50)
            time.sleep(0.2)
            self.buzzer_pwm.stop()
            time.sleep(0.2)
        self.buzzer_pwm.stop()

    def blink_red(self, duration=7):
        """빨간 LED 깜빡임"""
        for _ in range(duration * 2):
            GPIO.output(self.RED, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(self.RED, GPIO.LOW)
            time.sleep(0.5)

    def turn_on_green(self, duration=1):
        """초록색 LED 켜기"""
        GPIO.output(self.GREEN, True)
        time.sleep(duration)
        GPIO.output(self.GREEN, False)

    def turn_on_blue(self):
        """파란색 LED 켜기 (인식 중)"""
        GPIO.output(self.BLUE, True)

    def turn_off_blue(self):
        """파란색 LED 끄기 (인식 완료)"""
        GPIO.output(self.BLUE, False)

    def set_servo_pos(self, degree):
        """서보 모터를 특정 각도로 이동"""
        duty = self.SERVO_MIN_DUTY + (degree * (self.SERVO_MAX_DUTY - self.SERVO_MIN_DUTY) / 180.0)
        self.servo.ChangeDutyCycle(duty)
        time.sleep(0.5)  # 안정화 대기
        self.servo.ChangeDutyCycle(0)  # PWM 신호 끄기

    def control_servo(self):
        """서보 모터 동작: 90도 회전 -> 7초 대기 -> 원위치"""
        self.set_servo_pos(90)  # 90도로 이동
        time.sleep(7)  # 7초 대기
        self.set_servo_pos(0)  # 원위치로 복귀

    def display_number(self, number):
        """FND에 5초 동안 번호 표시"""
        s = ''.join([char if char in self.num else ' ' for char in str(number).rjust(4)])

        end_time = time.time() + 5
        while time.time() < end_time:
            for digit in range(4):
                for loop in range(7):
                    GPIO.output(self.segments[loop], self.num[s[digit]][loop])
                GPIO.output(self.digits[digit], 0)
                time.sleep(0.002)
                GPIO.output(self.digits[digit], 1)

    def run_fnd_and_servo(self, number):
        """FND와 서보모터를 동시에 작동"""
        # FND 스레드
        fnd_thread = threading.Thread(target=self.display_number, args=(number,))
        # 서보모터 스레드
        servo_thread = threading.Thread(target=self.control_servo)

        # 스레드 시작
        fnd_thread.start()
        servo_thread.start()

        # 스레드 완료 대기 (필요하면 사용)
        fnd_thread.join()
        servo_thread.join()

    def cleanup(self):
        """GPIO 리소스 정리"""
        self.servo.stop()
        GPIO.cleanup()
