#humid/temperature & light sensor
#TO DO: turn on led light

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

# Edit this to suit your GPIO pin for Temp/Humid Sensor
# Board.DX where X is GPIO number like GPIO4 is D4, GPIO24 is D24
dht_device = adafruit_dht.DHT11(board.D4)

class MQTTClient:
    def __init__(self, server, port):
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.connect(server, port, 60)


    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")
        # Subscribe to a topic 
        self.mqttc.subscribe("home/temp")

    def on_message(self, client, userdata, msg):
        # Attempt to parse the message payload as JSON
        message = json.loads(msg.payload.decode())
        print(msg.topic, message)

    def start(self):
        self.mqttc.loop_start()

    def stop(self):
        self.mqttc.loop_stop()
        # Clean up
        # GPIO.cleanup()

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
            uvLight = ltr

            print("Temp:{:.1f} C / {:.1f} F    Humidity: {}%".format(temperature_c, temperature_f, humidity))
            print("UV:{:.2f}".format(uvLight.uvi))
            # Publish the temp, humid and UV index
            self.publish(topic, {
                'temp': "{:.2f}".format(temperature_c), 
                'humid':"{}%".format(humidity), 
                'uv':"{:.2f}".format(uvLight.uvi)
            })

            # FOR TESTING (HARD CODED DATA, for work WITHOUT sensors)
            # print("Temp:{:.1f} C / {:.1f} F    Humidity: {}%".format(30.50, 86.9, 55.55))
            # self.publish(topic, {'temp': "{:.2f}".format(30.50), 'humid':"{}%".format(55.55)})

        except RuntimeError as err:
            print(err.args[0])


if __name__ == "__main__":
    # Main method
    # Replace "test.mosquitto.org" with the Broker IP such as "192.xxx.xxx.xxx" or wtv is the ip
    client = MQTTClient("test.mosquitto.org", 1883)

    client.start()
    try:
        while True:
            # Topic used is "home/temp", able to change depending on topic needed
            client.readSensors("home/temp")
            time.sleep(1)  # Delay for 1 second before reading again
    except KeyboardInterrupt:
        client.stop()
