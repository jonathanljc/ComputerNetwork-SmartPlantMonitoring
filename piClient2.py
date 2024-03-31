# humid/temperature & light sensor
# TO DO: turn on led light

# For Temperature and Humidity sensor:
# pip3 install adafruit-circuitpython-dht
# sudo apt-get install libgpiod2
# pip3 install adafruit-blinka

# For UV Light sensor
# pip3 install adafruit-circuitpython-ltr390

import time
import adafruit_dht
import adafruit_ltr390
import board
import paho.mqtt.client as mqtt
import json
import RPi.GPIO as GPIO

# Edit this to suit your GPIO pin for Temp/Humid Sensor
# Board.DX where X is GPIO number like GPIO4 is D4, GPIO24 is D24
dht_device = adafruit_dht.DHT11(board.D22)

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)
GPIO.setup(25, GPIO.OUT)


class MQTTClient:
    automaticMode = 1

    def __init__(self, server, port):
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.connect(server, port, 60)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")
        # Subscribe to a topic
        self.mqttc.subscribe("home/sensorsF")

    def on_message(self, client, userdata, msg):
        # Attempt to parse the message payload as JSON
        message = msg.payload.decode()
        print(msg.topic, message)

        if message == "manual":
            self.automaticMode = 0
            GPIO.output(23, GPIO.LOW)
            GPIO.output(24, GPIO.LOW)
            GPIO.output(25, GPIO.LOW)
        if message == "auto":
            self.automaticMode = 1
            GPIO.output(23, GPIO.LOW)
            GPIO.output(24, GPIO.LOW)
            GPIO.output(25, GPIO.LOW)

        if self.automaticMode == 0:
            if message == "red":
                if GPIO.input(23) == 0:
                    GPIO.output(23, GPIO.HIGH)
                else:
                    GPIO.output(23, GPIO.LOW)
            elif message == "green":
                if GPIO.input(24) == 0:
                    GPIO.output(24, GPIO.HIGH)
                else:
                    GPIO.output(24, GPIO.LOW)
            elif message == "blue":
                if GPIO.input(25) == 0:
                    GPIO.output(25, GPIO.HIGH)
                else:
                    GPIO.output(25, GPIO.LOW)
            elif message == "off":
                GPIO.output(23, GPIO.LOW)
                GPIO.output(24, GPIO.LOW)
                GPIO.output(25, GPIO.LOW)

    def start(self):
        self.mqttc.loop_start()

    def stop(self):
        self.mqttc.loop_stop()
        # Clean up
        GPIO.cleanup()

    # Method to publish json with topic to broker
    def publish(self, topic, message):
        self.mqttc.publish(topic, json.dumps(message))

    # Read temperature and humidity and UV light from sensor and publishes the data
    def readSensors(self, topic):
        try:
            # Sets up temperature & humidity sensor
            temperature_c = dht_device.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = dht_device.humidity

            # Sets up light sensor
            i2c = board.I2C()
            ltr = adafruit_ltr390.LTR390(i2c)

            print(
                "Temp:{:.2f} C || Humidity: {:.2f}% || Lux: {:.2f}".format(
                    temperature_c, humidity, ltr.lux
                )
            )
            # Publish the temp, humid and UV index
            self.publish(
                topic,
                {
                    "temp": "{:.2f}".format(temperature_c),
                    "humid": "{:.2f}".format(humidity),
                    "lux": "{:.2f}".format(ltr.lux),
                },
            )

            if self.automaticMode == 1:
                if ltr.lux <= 100:
                    GPIO.output(23, GPIO.HIGH)
                    GPIO.output(24, GPIO.LOW)
                    GPIO.output(25, GPIO.LOW)
                elif ltr.lux <= 300:
                    GPIO.output(23, GPIO.LOW)
                    GPIO.output(24, GPIO.HIGH)
                    GPIO.output(25, GPIO.LOW)
                elif ltr.lux <= 500:
                    GPIO.output(23, GPIO.LOW)
                    GPIO.output(24, GPIO.LOW)
                    GPIO.output(25, GPIO.HIGH)
                else:
                    GPIO.output(23, GPIO.LOW)
                    GPIO.output(24, GPIO.LOW)
                    GPIO.output(25, GPIO.LOW)

        except RuntimeError as err:
            print(err.args[0])


if __name__ == "__main__":
    # Main method
    # Replace the address with the Broker IP such as "192.xxx.xxx.xxx" or wtv is the ip
    client = MQTTClient("localhost", 1883)

    client.start()
    try:
        while True:
            # Topic used is "home/temp", able to change depending on topic needed
            client.readSensors("home/sensorsF")
            time.sleep(1)  # Delay for 1 second before reading again
    except KeyboardInterrupt:
        client.stop()
