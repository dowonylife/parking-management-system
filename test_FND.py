import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# GPIO ports for the 7seg pins
segments = (11, 4, 23, 8, 7, 10, 13, 25)

# Set up each segment pin as output
for segment in segments:
    GPIO.setup(segment, GPIO.OUT)
    GPIO.output(segment, 0)

# GPIO ports for the digit 0-3 pins
digits = (22, 27, 17, 24)

# Set up each digit pin as output
for digit in digits:
    GPIO.setup(digit, GPIO.OUT)
    GPIO.output(digit, 1)

# Define number patterns for the 7-segment display
num = {
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

try:
    while True:
        # Set the custom number you want to display, for example '1234'
        n = '1234'  # You can change this to any 4-digit number you want

        # Ensure the number is 4 digits (pad with spaces if needed)
        s = str(n).rjust(4)

        for digit in range(4):
            for loop in range(0, 7):
                GPIO.output(segments[loop], num[s[digit]][loop])

                # Control the decimal point (if desired)
                if (int(time.ctime()[18:19]) % 2 == 0) and (digit == 1):
                    GPIO.output(25, 1)  # Turn on decimal point on second digit
                else:
                    GPIO.output(25, 0)  # Turn off decimal point

            # Activate the current digit
            GPIO.output(digits[digit], 0)

            # Small delay for flicker effect
            time.sleep(0.001)

            # Deactivate the current digit
            GPIO.output(digits[digit], 1)

finally:
    GPIO.cleanup()
