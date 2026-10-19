import paho.mqtt.client as mqtt
import time
import random

broker_address = "test.mosquitto.org"
port = 1883
topic_rainfall = "students/weather/sensor2/rainfall"

client = mqtt.Client("Rain_Gauge_2")
client.connect(broker_address, port)

print("Rain Gauge 2 connected. Publishing data...")

try:
    while True:
        rainfall = round(random.uniform(0.0, 0.5), 2)

        client.publish(topic_rainfall, str(rainfall))
        
        print(f"Published from Sensor 2: Rainfall={rainfall} inches")
        
        time.sleep(7) # Use a different interval to show async behavior

except KeyboardInterrupt:
    print("Rain Gauge 2 stopped.")
    client.disconnect()