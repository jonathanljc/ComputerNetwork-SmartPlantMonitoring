import time
from paho.mqtt.client import ReasonCode
import paho.mqtt.client as mqtt


def on_publish(client, userdata, mid, reason_code, properties):
    # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3
    try:
        userdata.remove(mid)
    except KeyError:
        print("on_publish() is called with a mid not present in unacked_publish")
        print("This is due to an unavoidable race-condition:")
        print("* publish() return the mid of the message sent.")
        print("* mid from publish() is added to unacked_publish by the main thread")
        print("* on_publish() is called by the loop_start thread")
        print(
            "While unlikely (because on_publish() will be called after a network round-trip),"
        )
        print(" this is a race-condition that COULD happen")
        print("")
        print(
            "The best solution to avoid race-condition is using the msg_info from publish()"
        )
        print(
            "We could also try using a list of acknowledged mid rather than removing from pending list,"
        )
        print("but remember that mid could be re-used !")


def on_connect(client, userdata, flags, rc: ReasonCode, properties: dict):
    print("CONNACK received with code %d." % (rc.value))


unacked_publish = set()
mqttc = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5
)
mqttc.on_publish = on_publish
mqttc.on_connect = on_connect

mqttc.user_data_set(unacked_publish)
mqttc.connect("localhost", 1883, 60)
mqttc.loop_start()

print("Press Ctrl+C to exit the loop")

try:
    wave = 0
    do_substract = False
    while True:
        if wave == 100:
            do_substract = True
        elif wave == 0:
            do_substract = False
        if do_substract:
            wave -= 1
        else:
            wave += 1

        msg_info = mqttc.publish("test/subscriber", wave, qos=2)
        print(wave)
        unacked_publish.add(msg_info.mid)
        msg_info.wait_for_publish()

        while len(unacked_publish):
            time.sleep(0.1)
        time.sleep(1)
except KeyboardInterrupt:
    # User has pressed Ctrl+C, exit the loop
    pass

mqttc.disconnect()
mqttc.loop_stop()
