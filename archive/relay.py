import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import json

class MQTTClient:
    def __init__(self):
        self.mqttc = mqtt.Client()
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.connect("192.168.1.225", 1883, 60)  # MQTT broker address and port
        # Set the GPIO pin for the relay
        self.relay_pin = 4
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        # Ensure the relay is initially off
        GPIO.output(self.relay_pin, GPIO.LOW)

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        # Subscribe to the topic
        self.mqttc.subscribe("test/relay")

    def on_message(self, client, userdata, msg):
        try:
            # Decode and parse the message payload
            message = json.loads(msg.payload.decode())
            print(msg.topic, message)
            # Handle relay topic
            if msg.topic == 'test/relay':
                # Control the relay based on the message
                self.control_relay(message)
            else:
                print(f"Received message on unhandled topic: {msg.topic}")
        except json.JSONDecodeError:
            print(f"Could not parse message payload as JSON: {msg.payload}")

    def control_relay(self, message):
        # Assuming the message is a dictionary with a 'state' key
        state = message.get('state')
        if state == 'ON':
            GPIO.output(self.relay_pin, GPIO.HIGH)
            print("Relay turned ON")
        elif state == 'OFF':
            GPIO.output(self.relay_pin, GPIO.LOW)
            print("Relay turned OFF")
        else:
            print(f"Invalid state: {state}")

    def start(self):
        self.mqttc.loop_forever()

if __name__ == "__main__":
    # Usage
    client = MQTTClient()
    client.start()
