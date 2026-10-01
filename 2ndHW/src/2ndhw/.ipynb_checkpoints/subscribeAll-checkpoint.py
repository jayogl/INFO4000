import time
import paho.mqtt.client as mqtt

# Configuration
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_WILDCARD = "weather/#"  # Subscribes to all weather sub-topics

# Global counter for tracking received data points
data_count = 0

# Callback when connecting to broker
def on_connect(client, userdata, flags, rc):
  if rc == 0:
    print("Connected to broker! Subscribing to all weather topics...")
    client.subscribe(TOPIC_WILDCARD)
  else:
    print(f"Failed to connect, return code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
  global data_count
  data_count += 1
  payload_str = msg.payload.decode("utf-8")
  print(
      f"[{data_count}/50] Received on '{msg.topic}':"
      f" {payload_str}"
  )

# Initialize client and attach callbacks
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect and start background processing loop
client.connect(BROKER, PORT)
client.loop_start()

# Main thread waits until 50 data points are received
try:
  while data_count &lt; 50:
    time.sleep(0.1)  # Pause main thread while background thread listens

  print("\nReached 50 data points! Stopping subscriber...")
  client.loop_stop()  # Stop background thread
  client.disconnect()
  print("Subscriber disconnected successfully.")
except KeyboardInterrupt:
  client.loop_stop()
  client.disconnect()