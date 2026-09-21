"""
Key Components of an MQTT Subscriber Template:

1. Import necessary libraries: You'll need an MQTT client library, such as the Paho MQTT client in Python.
2.Define callback functions:
    - on_connect(client, userdata, flags, rc): This function is called when the client successfully connects to the broker. You'd typically subscribe to topics within this callback.
    - on_message(client, userdata, msg): This function is triggered when a message is received on a subscribed topic.
3.Instantiate the client: Create a client object, providing a unique client ID.
4. Set up authentication (optional): Provide a username and password if the broker requires them.
5. Connect to the broker: Use the client's connect method, providing the broker's address and port.
6. Start the network loop: The loop_start() or loop_forever() method keeps the client connected and handles network traffic, ensuring callbacks are triggered.

"""

import paho.mqtt.client as mqtt
import numpy as np
import time

# Broker address, port number and topic definitions
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = [
    ("my/sensor/data/text", 0),
    ("my/sensor/data/json", 0),
    ("my/sensor/data/binary", 1),
]

test_variable = 10

# Create a new MQTT client instance
client = mqtt.Client()


# Callback function for when the client connects (rc = return code and 0 means successful)
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to the topic after successful connection
        client.subscribe(TOPIC)
    else:
        print(f"Failed to connect, return code {rc}\n")


# Callback function for when a message is received
def on_message(client, userdata, msg):
    if msg.topic == "my/sensor/data/binary":
        print(
            "Received image data. This would typically be saved to a file or processed by an image library."
        )
        # Save to a file (simplified, error handling omitted)
        with open("received_image.jpg", "wb") as f:
            f.write(msg.payload)
    else:
        # Decode to a UTF-8 string
        payload_str = msg.payload.decode("utf-8")
        print(f"Received message on topic '{msg.topic}': {payload_str}")


# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker (add username/password if needed)
try:
    client.connect(BROKER, PORT)
except Exception as e:
    print(f"Could not connect to broker: {e}")
    exit()

# Start the network loop to process callbacks and handle reconnections
# loop_start() runs in a separate thread, allowing other code to run

#client.loop_start()

client.loop_forever()

try:
    while True:
        # You can add other code here to run periodically
        print(
            f"Rest of the program will run while MQTT communication happens in a separate thread: {test_variable}"
        )
        time.sleep(1)  # Pauses the main thread for 1 second
except KeyboardInterrupt:
    print("Program stopped by user.")

"""
IMPORTANT NOTES:

In an MQTT client application, network activity like sending messages, receiving data, 
and handling connection acknowledgements must happen continuously. 

The Paho Python MQTT client library offers a few ways to achieve this:

loop(): 
This method must be called manually and regularly by your program. If you forget to call it, or if your program is busy with other tasks, network activity will be delayed.

loop_forever(): This is a blocking call that takes over the main thread. It is useful for simple programs that do nothing but subscribe to an MQTT topic and wait for messages. 
The program's execution will not proceed past this line.

loop_start(): This is the most flexible option. It creates and runs the network loop in a new, dedicated background thread. 
It returns control to your main program immediately, which can then perform other work. 

How does loop_start() work?

1. Starts a new thread: When you call client.loop_start(), the MQTT client object spawns a new thread.
2. Calls loop() automatically: This new thread repeatedly calls the MQTT client's internal loop() function to manage all the network traffic.
3. Frees the main thread: Your main program is not blocked and can execute other code, such as performing calculations, handling user input, or running a publishing loop.
4. Enables asynchronous behavior: Since network operations happen in a separate thread, any callback functions (like on_message) are also executed within that thread. This allows your application to react to incoming messages asynchronously.
5. Handles reconnections: A key benefit of loop_start() is that it automatically attempts to reconnect to the broker if the connection is lost. 
6. To stop the background loop, you simply call client.loop_stop() or client.disconnect(). 
7. Important to remember that if your main program ends, the loop will anyways stop. 
   If you want the main program to stay alive because it has to do something everytime data comes in, run it in a while loop.

"""
