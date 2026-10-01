import json
import random
import time
import paho.mqtt.client as mqtt

# Configuration
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "weather/rainfall"

# Initialize MQTT Client
client = mqtt.Client()
client.connect(BROKER, PORT)
print(f"Connected to MQTT broker: {BROKER}")

try:
    while True:
        # Generate random rainfall reading
        rainfall = round(random.uniform(0.0, 2.0), 2)  # Range: 0 - 2 inches

        # Format payload as JSON dictionary
        payload = json.dumps({"rainfall": rainfall})

        # Publish to broker
        client.publish(TOPIC, payload)
        print(f"[PUBLISHED] Topic: '{TOPIC}' | Payload: {payload}")

        time.sleep(1)  # Delay between publishes
except KeyboardInterrupt:
    print("\nRainfall publisher stopped.")
    client.disconnect()