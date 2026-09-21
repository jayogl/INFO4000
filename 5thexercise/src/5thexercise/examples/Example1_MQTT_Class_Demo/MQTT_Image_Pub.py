### MQTT Image Publisher ###

# Reads the image file in binary mode ("rb") and transmits the byte array over a topic.

# Practical Considerations

    # Broker Payload Limits: Default Mosquitto installations typically restrict message 
    # size via message_size_limit (often default ~1 MB or up to ~256 MB if configured). If you encounter dropped packets on high-resolution images, compress the image first or chunk the payload.

    # Avoid Base64: Sending raw binary via msg.payload avoids the ~33% size 
    # inflation and CPU overhead of Base64 encoding.
    
# Helps to compress the original image for fast and reliable transmission

import io
import threading
from PIL import Image
import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = TOPIC = "my_custom_image_feed_2026/camera/image"
INPUT_IMAGE_PATH = "Galaxy.jpg"

published_event = threading.Event()

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Connected to broker.")
    else:
        print(f"Connection failed: {reason_code}")

def on_publish(client, userdata, mid, reason_code=None, properties=None):
    print("Broker acknowledged receipt.")
    published_event.set()

# 1. Open, convert color format, resize, and compress
with Image.open(INPUT_IMAGE_PATH) as img:
    img = img.convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    byte_array = buf.getvalue()

print(f"Compressed byte size: {len(byte_array)} bytes")

# 2. Setup MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="in_memory_publisher")
client.on_connect = on_connect
client.on_publish = on_publish

client.connect(BROKER, PORT, keepalive=60)
client.loop_start()

# 3. Publish and wait for broker confirmation
client.publish(TOPIC, payload=byte_array, qos=1, retain=True)

# Wait up to 10 seconds for the broker acknowledgment
success = published_event.wait(timeout=10)
if success:
    print(f"Successfully transmitted {len(byte_array)} bytes.")
else:
    print("Publish timed out before broker acknowledged.")

client.loop_stop()
client.disconnect()