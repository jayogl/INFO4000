import json
import random
import time
import paho.mqtt.client as mqtt

# Configuration
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "jayog_info4000/weather/temp_humidity"

# Initialize MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="T&H_publisher_client")
client.connect(BROKER, PORT)
print(f"Connected to MQTT broker: {BROKER}")

try:
    while True:
        # Generate random readings within required ranges
        temp = round(random.uniform(50.0, 52.0), 2)  # Range: 50 - 52 F
        humidity = round(random.uniform(60.0, 80.0), 2)  # Range: 60 - 80 %

        # Format payload as JSON dictionary
        payload = json.dumps({"temperature": temp, "humidity": humidity})

        # Publish to broker
        client.publish(TOPIC, payload)
        print(f"[PUBLISHED] Topic: '{TOPIC}' | Payload: {payload}")

        time.sleep(1)  # Delay between publishes
except KeyboardInterrupt:
    print("\nTemperature/Humidity publisher stopped.")
    client.disconnect()