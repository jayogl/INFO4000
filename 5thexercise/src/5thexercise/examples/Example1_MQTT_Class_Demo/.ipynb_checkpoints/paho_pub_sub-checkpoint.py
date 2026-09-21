import paho.mqtt.client as mqtt #import the client1
import time

# Broker address
broker_address="test.mosquitto.org"     

# Connect to client
client = mqtt.Client() #create new instance

msg = [] # Container to store message data

# The callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to the topic 'TEMPERATURE'
    client.subscribe("TEMPERATURE")
    print("Subscribing to topic","TEMPERATURE")

# The callback for when a PUBLISH message is received from the server
def on_message(client, userdata, message):
    msg.append(message.payload.decode("utf-8"))
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

def on_log(client, userdata, level, buf):
    print("log: ",buf)
    

# Attach the callback functions
client.on_connect = on_connect
client.on_message=on_message 

print("connecting to broker")
client.connect(broker_address,port=1883) #connect to broker

client.loop_forever() #start the loop

