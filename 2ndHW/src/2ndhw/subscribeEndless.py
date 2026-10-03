import paho.mqtt.client as mqtt

# Configuration
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "jayog_info4000/weather/temp_humidity"

# Callback when connecting to broker
def on_connect(client, userdata, flags, rc):
  if rc == 0:
    print(f"Connected! Result code: {rc}", flush=True)
    client.subscribe(TOPIC)
    print(f"  -> Subscribed to: {TOPIC}")
  else:
    print(f"Failed to connect, return code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
  payload_str = msg.payload.decode("utf-8")
  print(f"[RECEIVED] Topic: '{msg.topic}' | Data: {payload_str}", flush=True)

# Initialize client and attach callbacks
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="endless_subscriber_client")
client.on_connect = on_connect
client.on_message = on_message

# Connect and start blocking loop
client.connect(BROKER, PORT)
print("Starting continuous loop_forever()... Press Ctrl+C to stop.")
client.loop_forever()  # Blocks main thread and listens continuously