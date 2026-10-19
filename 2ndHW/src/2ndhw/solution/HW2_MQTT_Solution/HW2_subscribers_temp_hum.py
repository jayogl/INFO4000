import paho.mqtt.client as mqtt

# MQTT Broker details
broker_address = "test.mosquitto.org"
port = 1883
topic_temp = "students/weather/sensor1/temperature"
topic_humid = "students/weather/sensor1/humidity"

def on_connect(client, userdata, flags, rc):
    print("Temp/Humidity Display connected with result code " + str(rc))
    client.subscribe(topic_temp)
    client.subscribe(topic_humid)

def on_message(client, userdata, msg):
    print(f"Temp/Humidity Display received message on topic '{msg.topic}': {msg.payload.decode()}")

def main():
    client = mqtt.Client("Temp_Humidity_Display_Forever")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_address, port)

    print("Temp/Humidity Display started. Running forever...")
    
    client.loop_forever()

    print("Temp/Humidity Display has finished.")

if __name__ == "__main__":
    main()