#sudo apt-get update
#sudo apt-get install pigpio python-pigpio python3-pigpio
#sudo systemctl enable pigpiod
#sudo systemctl start pigpiod
# to run script, python3 ultrasonic.py
import pigpio
import time
import statistics

# Constants
TRIG_PIN = 11
ECHO_PIN = 12
NUM_READINGS = 10
SPEED_OF_SOUND = 34300  # in cm/s
SLEEP_TIME = 1

# Initialize pigpio
pi = pigpio.pi()

# Set pin modes
pi.set_mode(TRIG_PIN, pigpio.OUTPUT)
pi.set_mode(ECHO_PIN, pigpio.INPUT)

# Reset trigger pin
pi.write(TRIG_PIN, 0)
time.sleep(2)

def get_distance():
    pi.write(TRIG_PIN, 1)
    time.sleep(0.00001)
    pi.write(TRIG_PIN, 0)

    start_time = time.time()
    while pi.read(ECHO_PIN) == 0:
        if time.time() - start_time > 1:  # Timeout after 1 second
            return None

    start_time = time.time()
    while pi.read(ECHO_PIN) == 1:
        if time.time() - start_time > 1:  # Timeout after 1 second
            return None

    stop_time = time.time()

    elapsed_time = stop_time - start_time
    distance = (elapsed_time * SPEED_OF_SOUND) / 2

    return distance

try:
    while True:
        distances = [get_distance() for _ in range(NUM_READINGS)]
        distances = [d for d in distances if d is not None]
        if distances:
            median_distance = statistics.median(distances)
            print(f"Median Distance: {median_distance:.2f} cm")
        else:
            print("No valid readings")
        time.sleep(SLEEP_TIME)
except KeyboardInterrupt:
    print("Measurement stopped by User")
    pi.stop()