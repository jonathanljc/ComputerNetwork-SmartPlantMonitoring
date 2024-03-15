import paho.mqtt.client as mqtt
import sqlite3

# Function to create the messages table in the database
def create_table():
    conn = sqlite3.connect('mqtt_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    message TEXT NOT NULL
                 )''')
    conn.commit()
    conn.close()

# Callback function when connection is established
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("home/moisture")
    client.subscribe("home/temperature")

# Callback function when message is received
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    save_to_database(msg.topic, msg.payload.decode())

# Callback function to save data to SQLite database
def save_to_database(topic, message):
    conn = sqlite3.connect('mqtt_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (topic, message) VALUES (?, ?)", (topic, message))
    conn.commit()
    conn.close()

# Create the messages table
create_table()

# Create an MQTT client instance
client = mqtt.Client()

# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT broker
client.connect("test.mosquitto.org", 1883, 60)

# Start the MQTT client loop (blocking)
client.loop_forever()
