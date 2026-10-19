import paho.mqtt.client as mqtt
import time
import random

broker_address = "test.mosquitto.org"
port = 1883
topic_temp = "students/weather/sensor1/temperature"
topic_humid = "students/weather/sensor1/humidity"

client = mqtt.Client("Weather_Station_1")
client.connect(broker_address, port)

print("Weather Station 1 (Temp/Humid) connected. Publishing data...")

try:
    while True:
        temperature = round(random.uniform(20.0, 30.0), 2)
        humidity = round(random.uniform(40.0, 60.0), 2)

        client.publish(topic_temp, str(temperature))
        client.publish(topic_humid, str(humidity))
        
        print(f"Published from Sensor 1: Temp={temperature}°C, Humid={humidity}%")
        
        time.sleep(5)

except KeyboardInterrupt:
    print("Weather Station 1 stopped.")
    client.disconnect()