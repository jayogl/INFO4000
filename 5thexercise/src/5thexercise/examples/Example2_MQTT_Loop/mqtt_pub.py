# Publisher of data

import paho.mqtt.client as mqtt
from random import randrange, uniform
import time
import json

mqttBroker = "test.mosquitto.org"
topic_text = "my/sensor/data/text"
topic_json = "my/sensor/data/json"
topic_binary = "my/sensor/data/binary"


client = mqtt.Client()

client.connect(mqttBroker, port=1883)

# --- Publishing Plain Text Payload ---
text_payload = "Hello, MQTT world!"
client.publish(topic_text, text_payload)
print(f"Published text: '{text_payload}' to topic: '{topic_text}'")

time.sleep(1)  # Give time for message to be sent

# --- Publishing JSON Payload ---
data = {"temperature": 25.5, "humidity": 60, "unit": "Celsius"}
json_payload = json.dumps(data)  # Convert dictionary to JSON string
client.publish(topic_json, json_payload)
print(f"Published JSON: '{json_payload}' to topic: '{topic_json}'")

time.sleep(1)

# --- Publishing Binary Payload (e.g., bytes from an image or sensor reading) ---
# 1. Read the image file in binary mode

with open("motor.jpg", "rb") as file:
    file_content = file.read()
client.publish(topic_binary, file_content)
print(f"Published binary data to topic: '{topic_binary}'")

time.sleep(2)  # Allow time for messages to be processed


