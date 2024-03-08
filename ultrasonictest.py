# This doens't use pigpio
import RPi.GPIO as GPIO
import time

try:
      GPIO.setmode(GPIO.BOARD)

      # need to use number on the board, not GPIO4 = 4. GPIO4 is pin 7, GPIO17 is pin 11, etc
      PIN_TRIGGER = 36
      PIN_ECHO = 31

      GPIO.setup(PIN_TRIGGER, GPIO.OUT)
      GPIO.setup(PIN_ECHO, GPIO.IN)

      GPIO.output(PIN_TRIGGER, GPIO.LOW)

      print("Waiting for sensor to settle")

      time.sleep(2)
            
      print("Calculating distance")

      while True:

            GPIO.output(PIN_TRIGGER, GPIO.HIGH)

            time.sleep(0.00001)

            GPIO.output(PIN_TRIGGER, GPIO.LOW)

            while GPIO.input(PIN_ECHO)==0:
                  pulse_start_time = time.time()
            while GPIO.input(PIN_ECHO)==1:
                  pulse_end_time = time.time()

            pulse_duration = pulse_end_time - pulse_start_time
            distance = round(pulse_duration * 17150, 2)
            print("Distance:",distance,"cm")
            time.sleep(1)

except KeyboardInterrupt:
      GPIO.cleanup()
