import time
import paho.mqtt.client as mqtt

# Configuration
BROKER = "test.mosquitto.org"
PORT = 1883

# Explicit list of topics to subscribe to
TOPICS = [
    ("jayog_info4000/weather/temp_humidity", 0),
    ("jayog_info4000/weather/rainfall", 0)
]

# Global counter for tracking received data points
data_count = 0

# Callback when connecting to broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected! Result code: {rc}", flush=True)
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"  -> Subscribed to: {topic}")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
    global data_count
    data_count += 1
    payload_str = msg.payload.decode("utf-8")
    print(f"[{data_count}/50] Received on '{msg.topic}': {payload_str}", flush=True)

# Initialize client and attach callbacks
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="50_subscriber_client")
client.on_connect = on_connect
client.on_message = on_message

# Connect and start background processing loop
client.connect(BROKER, PORT)
client.loop_start()

# Main thread waits until 50 data points are received
try:
    while data_count < 50:
        time.sleep(0.1)  # Pause main thread while background thread listens
    client.loop_stop()
    print("\nReached 50 data points! Stopping subscriber...")
    client.disconnect()
    print("Subscriber disconnected successfully.")
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()