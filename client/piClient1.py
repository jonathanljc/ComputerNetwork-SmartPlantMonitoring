import paho.mqtt.client as mqtt
import json
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from collections import deque
import numpy as np
import RPi.GPIO as GPIO
import threading
import pigpio
import statistics
# ultrasonic


class ClientOne:
    def __init__(self, server, port):
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.connect(server, port, 60)
        # Define the maximum and minimum ADC values estimation from the moisture sensor.
        self.MIN_ADC_VALUE = 12767
        self.MAX_ADC_VALUE = 32767
        # Define the weight for the exponential moving average.
        self.EMA_WEIGHT = 0.1
        # Define the maximum number of readings to store for outlier detection.
        self.MAX_READINGS = 100
        self.readings = deque(maxlen=self.MAX_READINGS)
        # Define the Z-score threshold for outlier detection.
        self.Z_THRESHOLD = 3
        # Set the GPIO pin to 17 for relay.
        self.RELAY_PIN = 17
        GPIO.setup(self.RELAY_PIN, GPIO.OUT)
        # Set the trigger pin to 11 for ultrasonic sensor
        self.TRIG_PIN = 11
        # Set the echo pin to 12 for ultrasonic sensor
        self.ECHO_PIN = 12
        # Set the sleep time to 1 second for ultrasonic sensor
        self.SLEEP_TIME = 1
        # Set the speed of sound to 34300 cm/s for ultrasonic sensor
        self.SPEED_OF_SOUND = 34300  # in cm/s
        # Set the number of readings to 10 for ultrasonic sensor
        self.NUM_READINGS = 5
        # Initialize the exponential moving average to None
        self.ema = None
        # Create the I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)
        # Create the ADS1115 ADC object
        self.ads = ADS.ADS1115(self.i2c)
        # Create an analog input channel for the ADS1115
        self.channel = AnalogIn(self.ads, ADS.P0)
        self.pi = pigpio.pi()  # using pigpio instead of gpio lib
        self.pi.set_mode(self.TRIG_PIN, pigpio.OUTPUT)
        self.pi.set_mode(self.ECHO_PIN, pigpio.INPUT)
        self.pi.write(self.TRIG_PIN, 0)
        time.sleep(
            2
        )  # sleep the system for 2s so that all pins are initialize before reading the sensors

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")
        # Subscribe to a topic
        self.mqttc.subscribe("relay/water")

    def on_message(self, client, userdata, msg):
        # Handle relay topic(rpi 1, water pump for webdashboard side when they turn on)
        if msg.topic == "relay/water":
            print(msg.payload)
            self.request_moisture()
        else:
            print(f"Received message on unhandled topic: {msg.topic}")

    def start(self):
        # Start a new thread to process network traffic.
        self.mqttc.loop_start()

    def stop(self):
        # Stop the network thread previously created with `loop_start()`.
        self.mqttc.loop_stop()
        # Clean up all GPIO pins.
        GPIO.cleanup()

    def publish(self, topic, message):
        self.mqttc.publish(topic, json.dumps(message), qos=2)

    def read_moisture_level(self):
        # Read the ADC value.
        adc_value = self.channel.value

        # Add the new reading to the deque.
        self.readings.append(adc_value)

        # If we have enough readings, check if the current reading is an outlier.
        if len(self.readings) == self.MAX_READINGS:
            mean = np.mean(self.readings)
            std_dev = np.std(self.readings)
            z_score = (adc_value - mean) / std_dev
            if abs(z_score) > self.Z_THRESHOLD:
                # This is an outlier, ignore it
                return None

        # If this is the first reading, initialize the EMA to the current reading
        if self.ema is None:
            self.ema = adc_value
        else:
            # Update the EMA
            self.ema = (self.EMA_WEIGHT * adc_value) + (
                (1 - self.EMA_WEIGHT) * self.ema
            )

        # Calculate the moisture level based on the EMA
        moisture_level = (
            (self.MAX_ADC_VALUE - self.ema) / (self.MAX_ADC_VALUE - self.MIN_ADC_VALUE)
        ) * 100

        # Ensure the moisture level is between 0 and 100%
        moisture_level = max(0, min(moisture_level, 100))

        return moisture_level

    def publish_moisture_level(self, topic):
        moisture_level = self.read_moisture_level()
        if moisture_level:
            moisture_level = round(moisture_level, 2)
            print("moisture", moisture_level)
            self.mqttc.publish(topic, moisture_level, qos=2)

    def request_moisture(self):
        # moisture_level = self.read_moisture_level()

        # if not (20 <= moisture_level <= 30):
        #     return

        print("Water Request Recieved!")

        # Currently, there is no check for spammed requests.
        threading.Thread(
            target=lambda: (
                print("Thread was created!"),
                GPIO.output(self.RELAY_PIN, GPIO.HIGH),
                print(
                    "GPIO",
                    self.RELAY_PIN,
                    "set to",
                    GPIO.HIGH,
                    "\nsleeping for 3 seconds",
                ),
                time.sleep(3),
                GPIO.output(self.RELAY_PIN, GPIO.LOW),
                print(self.RELAY_PIN, "set to", GPIO.LOW, "\nsleeping for 10 seconds"),
                time.sleep(10),
                print("Finished!"),
            )
        ).start()

    def get_distance(self):
        self.pi.write(self.TRIG_PIN, 1)
        time.sleep(0.00001)
        self.pi.write(self.TRIG_PIN, 0)

        start_time = time.time()
        while self.pi.read(self.ECHO_PIN) == 0:
            if time.time() - start_time > 1:
                return None

        start_time = time.time()
        while self.pi.read(self.ECHO_PIN) == 1:
            if time.time() - start_time > 1:
                return None

        stop_time = time.time()

        elapsed_time = stop_time - start_time
        distance = (elapsed_time * self.SPEED_OF_SOUND) / 2

        if distance > 20:
            return None

        return distance

    def read_and_publish_distance(self, topic):
        distances = [self.get_distance() for _ in range(self.NUM_READINGS)]
        distances = [d for d in distances if d is not None]
        if distances:
            median_distance = statistics.median(distances)
            # Cap the distance at 20cm and convert to a percentage
            capped_distance = min(median_distance, 20)
            percentage = (capped_distance / 20) * 100
            inverted_percentage = round(
                100 - percentage, 2
            )  # Invert the percentage, so that the nearer the water level it is the higher the percentage
            print("distance", inverted_percentage)
            self.mqttc.publish(topic, inverted_percentage, qos=2)
        else:
            print("No valid readings")
            self.mqttc.publish(topic, 0, qos=2)

    def publish_distance(self, topic):
        return


def main():
    server = "localhost" or "test.mosquitto.org"
    port = 1883
    client = ClientOne(server, port)
    client.start()
    try:
        while True:
            client.read_and_publish_distance("sensor/capacity")
            client.publish_moisture_level("sensor/moisture")
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop()


if __name__ == "__main__":
    main()
