import RPi.GPIO as GPIO
from time import sleep

# 서보 핀 설정
servoPin = 12
SERVO_MAX_DUTY = 12
SERVO_MIN_DUTY = 3

GPIO.setmode(GPIO.BOARD)
GPIO.setup(servoPin, GPIO.OUT)

# 서보 PWM 설정
servo = GPIO.PWM(servoPin, 50)  # 50Hz
servo.start(0)

def setServoPos(degree):
    duty = SERVO_MIN_DUTY + (degree * (SERVO_MAX_DUTY - SERVO_MIN_DUTY) / 180.0)
    servo.ChangeDutyCycle(duty)
    sleep(0.3)  # 안정화 대기
    servo.ChangeDutyCycle(0)  # PWM 신호를 끄기

if __name__ == "__main__":
    try:
        while True:
            input("Press Enter to move servo to 90 degrees...")
            setServoPos(90)

            input("Press Enter to move servo back to 0 degrees...")
            setServoPos(0)
    except KeyboardInterrupt:
        print("\nProgram terminated.")
    finally:
        servo.stop()
        GPIO.cleanup()
