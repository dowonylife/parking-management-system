import RPi.GPIO as GPIO
import time

BUZZER_PIN = 16

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

buzzer_pwm = GPIO.PWM(BUZZER_PIN, 440)


try:
    """
    KeyboardInterrupt 키를 누를 때까지 부저가 계속 삐삐삐 소리를 냄.
    """
    print("Press Enter to stop the beeping...")
    while True:
        buzzer_pwm.start(50)
        time.sleep(0.2)
        buzzer_pwm.stop()
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\nProgram terminated.")
finally:
    GPIO.cleanup()