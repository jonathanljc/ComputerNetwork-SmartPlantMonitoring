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

    def read_and_publish_moisture_level(self, topic):
        # Read the ADC value
        adc_value = self.channel.value
        # Add the new reading to the deque
        self.readings.append(adc_value)
        # If we have enough readings, check if the current reading is an outlier
        if len(self.readings) == self.max_readings:
            mean = np.mean(self.readings)
            std_dev = np.std(self.readings)
            z_score = (adc_value - mean) / std_dev
            if abs(z_score) > self.z_threshold:
                # This is an outlier, ignore it
                return
        # If this is the first reading, initialize the EMA to the current reading
        if self.ema is None:
            self.ema = adc_value
        else:
            # Update the EMA
            self.ema = (self.ema_weight * adc_value) + ((1 - self.ema_weight) * self.ema)
        # Calculate the moisture level based on the EMA
        moisture_level = ((self.max_adc_value - self.ema) / (self.max_adc_value - self.min_adc_value)) * 100
        # Ensure the moisture level is between 0 and 100%
        moisture_level = max(0, min(moisture_level, 100))
        # Publish the moisture level
        self.publish(topic, {'moisture_level': "{:.2f}".format(moisture_level)})
        if 20<=moisture_level<=30: #20-30% inclusive then activate water pump for 3seconds
            threading.Thread(target=lambda: (
                self.control_relay({'state': 'ON'}),
                time.sleep(3),
                self.control_relay({'state': 'OFF'}),
                time.sleep(10)
            )).start()
    # control the relay on server side tbc havent test yet. 
    def control_relay(self, message):
        # Assuming the message is a dictionary with a 'state' key
        state = message.get('state')
        if state == 'ON':
            GPIO.output(self.relay_pin, GPIO.HIGH)
        elif state == 'OFF':
            GPIO.output(self.relay_pin, GPIO.LOW)
        else:
            print(f"Invalid state: {state}")

if __name__ == "__main__":
    # Usage
    client = MQTTClient("test.mosquitto.org", 1883)#actual implementation use our network for now test with public broker
    client.start()
    try:
        while True:
            client.read_and_publish_moisture_level("home/moisture")
            time.sleep(1)  # Delay for 1 second before reading again
    except KeyboardInterrupt:
        client.stop()