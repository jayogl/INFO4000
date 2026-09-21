### MQTT Image Subscriber ###

# Subscribes to the topic and saves msg.payload directly to disk using binary write mode ("wb").

import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = TOPIC = "my_custom_image_feed_2026/camera/image"
OUTPUT_PATH = "received.jpg"

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected. Subscribing to topic...")
    client.subscribe(TOPIC, qos=1)

def on_message(client, userdata, msg):
    print(f"Received {len(msg.payload)} bytes. Writing to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "wb") as file:
        file.write(msg.payload)
    print("Image saved successfully.")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="image_subscriber")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, keepalive=60)

# Block and listen for incoming messages
client.loop_forever()