import RPi.GPIO as GPIO
import time

# GPIO 설정
GPIO.setmode(GPIO.BCM)

# RGB 핀 설정
RED = 6
GREEN = 19
BLUE = 26

GPIO.setup(RED, GPIO.OUT) # GPIO 17번을 RED의 출력으로 설정합니다.
GPIO.setup(GREEN, GPIO.OUT) # GPIO 27번을 GREEN의 출력으로 설정합니다.
GPIO.setup(BLUE, GPIO.OUT) # GPIO 22번을 BLUE의 출력으로 설정합니다.

# LED 제어 함수
def turn_on(color):
    if color == 'RED': # RED 실행시 1초 동안 점등 후 소등
        GPIO.output(RED, True)
        time.sleep(1)
        GPIO.output(RED, False)
    elif color == 'GREEN': # GREEN 실행시 1초 동안 점등 후 소등
        GPIO.output(GREEN, True)
        time.sleep(1)
        GPIO.output(GREEN, False)
    elif color == 'BLUE': # BLUE 실행시 1초 동안 점등 후 소등
        GPIO.output(BLUE, True)
        time.sleep(1)
        GPIO.output(BLUE, False)

# 메인 함수
try:
    while True: # R, G, B를 1초 단위로 켠다.
        turn_on('RED')
        time.sleep(1)
        turn_on('GREEN')
        time.sleep(1)
        turn_on('BLUE')
        time.sleep(1)
finally:
    GPIO.cleanup() # 모두 끈다.