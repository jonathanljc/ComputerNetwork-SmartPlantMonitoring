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
import pigpio as pi
import statistics
#ultrasonic

class MQTTClient:
    def __init__(self, server, port):
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.connect(server, port, 60)
        # Create the I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)
        # Create the ADS1115 ADC object
        self.ads = ADS.ADS1115(self.i2c)
        # Create an analog input channel for the ADS1115
        self.channel = AnalogIn(self.ads, ADS.P0)
        # Define the maximum and minimum ADC values estimation from the moisture sensor
        self.min_adc_value = 12767
        self.max_adc_value = 32767 
        # Define the weight for the exponential moving average
        self.ema_weight = 0.1
        # Initialize the exponential moving average to None
        self.ema = None
        # Define the maximum number of readings to store for outlier detection
        self.max_readings = 100
        self.readings = deque(maxlen=self.max_readings)
        # Define the Z-score threshold for outlier detection
        self.z_threshold = 3
        # Set the GPIO pin to 17 for relay
        self.relay_pin = 17
        GPIO.setup(self.relay_pin, GPIO.OUT)
        # Set the trigger pin to 11 for ultrasonic sensor
        self.TRIG_PIN = 11
        # Set the echo pin to 12 for ultrasonic sensor
        self.ECHO_PIN = 12
        # Set the sleep time to 1 second for ultrasonic sensor
        self.SLEEP_TIME = 1
        # Set the speed of sound to 34300 cm/s for ultrasonic sensor
        self.SPEED_OF_SOUND = 34300 # in cm/s
        # Set the number of readings to 10 for ultrasonic sensor
        self.NUM_READINGS = 10

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")
        # Subscribe to a topic 
        self.mqttc.subscribe("onrelay")

    def on_message(self, client, userdata, msg):
        try:
            # Attempt to parse the message payload as JSON
            message = json.loads(msg.payload.decode())
            print(msg.topic, message)
            # Handle relay topic(rpi 1, water pump for webdashboard side when they turn on)
            if msg.topic == 'onrelay':
                # Control the relay based on the message
                self.control_relay(message)
            else:
                print(f"Received message on unhandled topic: {msg.topic}")
        except json.JSONDecodeError:
            print(f"Could not parse message payload as JSON: {msg.payload}")

    def start(self):
        self.mqttc.loop_start()

    def stop(self):
        self.mqttc.loop_stop()
        # Clean up
        GPIO.cleanup()

    def publish(self, topic, message):
        self.mqttc.publish(topic, json.dumps(message))

    
            
    def get_distance(self):
        pi.write(self.TRIG_PIN, 1)
        time.sleep(0.00001)
        pi.write(self.TRIG_PIN, 0)
        
        start_time = time.time()
        while pi.read(self.ECHO_PIN) == 0:
            if time.time() - start_time > 1: # Timeout after 1 second
                return None
            
        start_time = time.time()
        while pi.read(self.ECHO_PIN) == 1:
            if time.time() - start_time > 1: # Timeout after 1 second
                return None
        
        stop_time = time.time()
        
        elapsed_time = stop_time - start_time
        distance = (elapsed_time * self.SPEED_OF_SOUND) / 2
        
        return distance
            
    def read_and_publish_distance(self, topic):
        # Set pin modes
        pi.set_mode(self.TRIG_PIN, pigpio.OUTPUT)
        pi.set_mode(self.ECHO_PIN, pigpio.INPUT)
        
        # Reset trigger pin
        pi.write(self.TRIG_PIN, 0)
        time.sleep(2)
        
        try:
            while True:
                distances = [self.get_distance() for _ in range(self.NUM_READINGS)]
                distances = [d for d in distances if d is not None]
                if distances:
                    median_distance = statistics.median(distances)
                    print(f"Median Distance: {median_distance:.2f} cm")
                    self.publish(topic, {'distance': "{:.2f}".format(median_distance)})
                else:
                    print("No valid readings")
                time.sleep(self.SLEEP_TIME)
        except KeyboardInterrupt:
            print("Measurement stopped by User")
            pi.stop()
        
        

if __name__ == "__main__":
    # Usage
    client = MQTTClient("test.mosquitto.org", 1883)#actual implementation use our network for now test with public broker
    client.start()
    try:
        while True:
            client.read_and_publish_distance("home/distance")
            
            time.sleep(1)  # Delay for 1 second before reading again
    except KeyboardInterrupt:
        client.stop()