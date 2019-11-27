"""This program receives temperature and humidity measurements from RuuviTag sensors using MQTT and shows them on a Waveshare 2.7 inch e-Paper HAT.

Copyright (C) Koen Vervloesem 2019

License: MIT
"""
from datetime import datetime
import socket
import time

import paho.mqtt.client as mqtt
from PIL import ImageFont

import epd2in7b_fast_lut as epd2in7b


# Settings for bt-mqtt-gateway
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "RuuviTagPaper"

GATEWAY_PREFIX = "bt-mqtt-gateway"
RUUVITAG_PREFIX = "ruuvitag"

MQTT_TOPIC_TEMP = ("/").join([GATEWAY_PREFIX, RUUVITAG_PREFIX, "+", "temperature"])
MQTT_TOPIC_HUM = ("/").join([GATEWAY_PREFIX, RUUVITAG_PREFIX, "+", "humidity"])

# Settings for the ePaper screen
COLORED = 1
UNCOLORED = 0

FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SIZE = 18
FONT = ImageFont.truetype(FONT_FILE, FONT_SIZE)

SENSOR_FORMAT = "{:^4}   {:4.1f} °C  {:4.1f} %H"
TIME_FORMAT = "%Y-%m-%d %H:%M"
CHARACTER_WIDTH = 24

BEGIN_POS = 10

INIT_TEMP = 0.0
INIT_HUM = 0.0

# Dictionary with the sensor names and their values
sensor_values = {
    "tag1": {"temperature": INIT_TEMP, "humidity": INIT_HUM},
    "tag2": {"temperature": INIT_TEMP, "humidity": INIT_HUM},
    "tag3": {"temperature": INIT_TEMP, "humidity": INIT_HUM},
    "tag4": {"temperature": INIT_TEMP, "humidity": INIT_HUM},
}


def tag_from_topic(mqtt_topic):
    """Extract the RuuviTag's name from the MQTT topic."""
    return mqtt_topic.split("/")[2]


def property_from_topic(mqtt_topic):
    """Extract the RuuviTag's property from the MQTT topic."""
    return mqtt_topic.split("/")[3]


def get_local_ip():
    """Get the machine's local IP address."""
    # Based on https://stackoverflow.com/a/28950776/10368577
    # This *should* work on Linux, macOS and Windows.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        ip_address = s.getsockname()[0]
    except OSError:
        ip_address = "No network"
    finally:
        s.close()

    return ip_address


def on_connect(client, userdata, flags, rc):
    """Subscribe to the right MQTT topics after connecting."""
    print("Connected with result code " + str(rc))
    client.subscribe([(MQTT_TOPIC_TEMP, 0), (MQTT_TOPIC_HUM, 0)])


def on_message(client, userdata, message):
    """Register the sensor values received with MQTT."""
    tag = tag_from_topic(message.topic)
    prop = property_from_topic(message.topic)

    number = float(message.payload.decode("utf-8"))

    print("Message received: {}/{} = {}".format(tag, prop, number))

    sensor_values[tag][prop] = number


def main():
    # Initialize MQTT connection
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(MQTT_HOST, MQTT_PORT)

    # Initialize ePaper screen
    epd = epd2in7b.EPD()
    epd.init()
    epd.set_rotate(epd2in7b.ROTATE_270)

    while True:
        mqtt_client.loop_start()
        time.sleep(30)  # Update screen every 30 seconds
        mqtt_client.loop_stop()

        print("Update screen")

        # Clear the frame buffers
        frame_black = [0] * int(epd.width * epd.height / 8)
        frame_red = [0] * int(epd.width * epd.height / 8)

        position = BEGIN_POS

        # Show date and time
        epd.draw_string_at(
            frame_black,
            4,
            position,
            datetime.now().strftime(TIME_FORMAT).center(CHARACTER_WIDTH),
            FONT,
            COLORED,
        )
        position = position + FONT_SIZE + 2

        # Draw horizontal bar
        epd.draw_filled_rectangle(
            frame_red, 0, position + 5, epd.width, position + 8, COLORED
        )
        position = position + FONT_SIZE + 2

        # Draw sensor values to the buffer tag by tag
        for tag, values in sensor_values.items():
            epd.draw_string_at(
                frame_black,
                4,
                position,
                SENSOR_FORMAT.format(
                    tag.capitalize(), values["temperature"], values["humidity"]
                ),
                FONT,
                COLORED,
            )
            position = position + FONT_SIZE + 2

        # Draw horizontal bar
        epd.draw_filled_rectangle(
            frame_red, 0, position + 5, epd.width, position + 8, COLORED
        )
        position = position + FONT_SIZE + 2

        # Show IP address
        ip_address = get_local_ip()
        epd.draw_string_at(
            frame_black, 4, position, ip_address.center(CHARACTER_WIDTH), FONT, COLORED
        )

        # Display the frame
        epd.display_frame(frame_black, frame_red)


if __name__ == "__main__":
    main()
