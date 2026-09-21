# Publisher of data

import paho.mqtt.client as mqtt 
from random import randrange, uniform
import time

mqttBroker = "test.mosquitto.org"
client = mqtt.Client()


client.connect(mqttBroker,port=1883) 

while True:
    randNumber = uniform(20.0, 21.0)
    client.publish("TEMPERATURE", randNumber)
    print("Just published " + str(randNumber) + " to topic TEMPERATURE")
    time.sleep(1)


# Initialize the MQTT client with the specified callback API version if using callback
# client = mqtt.Client(
#     mqtt.CallbackAPIVersion.VERSION2,  # Specify the API version
#     client_id="Temperature_Inside",    # Your client ID
#     protocol=mqtt.MQTTv311             # Optional: Specify MQTT protocol version
# )