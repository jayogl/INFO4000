import paho.mqtt.client as mqtt
import time

# MQTT Broker details
broker_address = "test.mosquitto.org"
port = 1883

# Define the data point limit
DATA_POINT_LIMIT = 50
message_count = 0

# The wildcard topic filter to subscribe to all weather sensors
topic_all_weather = "students/weather/#"

def on_connect(client, userdata, flags, rc):
    print("Weather Dashboard connected with result code " + str(rc))
    # Subscribing to a wildcard topic
    client.subscribe(topic_all_weather)

def on_message(client, userdata, msg):
    global message_count
    message_count += 1
    
    print(f"Weather Dashboard received message ({message_count}/{DATA_POINT_LIMIT}) on topic '{msg.topic}': {msg.payload.decode()}")

def main():
    global message_count
    
    client = mqtt.Client("Limited_Weather_Dashboard")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_address, port)

    # Start the network loop in a background thread
    client.loop_start()

    print("Weather Dashboard started. Waiting for messages...")

    try:
        while message_count < DATA_POINT_LIMIT:
            # Main thread sleeps while the MQTT loop runs in the background
            time.sleep(1)
        
        print("Data point limit reached. Stopping...")
        
    except KeyboardInterrupt:
        print("Program interrupted by user.")
        
    finally:
        # Stop the network loop and disconnect
        client.loop_stop()
        client.disconnect()

    print("Weather Dashboard has finished.")

if __name__ == "__main__":
    main()