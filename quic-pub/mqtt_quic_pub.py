"""
MQTT_CLUSTER_IP => String, IP address of the MQTT broker
MQTT_CLUSTER_PORT => Int, port of the MQTT broker, quic default is 14567
MQTT_TOPIC => String topic in which messages will be sent. Can have multiple levels and use wildcards (+, #)
MQTT_QOS => [0,1,2], MQTT Quality of service
MQTT_SECRETS => kubernetes secret Username and password 
MQTT_MESSAGE_NUM => Int, messages to be sent
MQTT_MESSAGE_SIZE => Int, message size mimic QoS of applications
MQTT_MESSAGE_FREQ_MS => Int, MQTT message frequency measured in milliseconds
"""
import pynng
import os
import asyncio
import random
import string
import logging
import datetime

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

CONN = 1
PUB = 3
SUB = 8

delay = int(os.getenv("CONTAINER_DELAY_S"))
mqtt_cluster_ip = os.getenv("MQTT_CLUSTER_IP")
mqtt_cluster_port = os.getenv("MQTT_CLUSTER_PORT")
mqtt_topic = os.getenv("MQTT_TOPIC")
mqtt_qos = int(os.getenv("MQTT_QOS"))
mqtt_secrets = os.getenv("MQTT_SECRETS")
mqtt_message_num = int(os.getenv("MQTT_MESSAGE_NUM"))
mqtt_min_message_size = int(os.getenv("MQTT_MIN_MESSAGE_SIZE"))
mqtt_max_message_size = int(os.getenv("MQTT_MAX_MESSAGE_SIZE"))
mqtt_message_freq_ms = int(os.getenv("MQTT_MESSAGE_FREQ_MS")) / 1000
mqtt_client_id = os.getenv("POD_NAME")

def build_payload(mqtt_min_message_size, mqtt_max_message_size):
    time = datetime.datetime.now()
    message_size = random.randint(mqtt_min_message_size, mqtt_max_message_size)
    payload = (''.join(random.choice(string.ascii_uppercase + string.digits) 
                      for _ in range(message_size)) + "#" + str(time))
    return payload

def build_topic(mqtt_topic, mqtt_client_id):
    client_number = mqtt_client_id.split("-")[5]
    topic = mqtt_topic + "/" + client_number
    return topic

def build_conn_message(mqtt_secrets):
    connmsg = pynng.Mqttmsg()
    connmsg.set_packet_type(CONN)  # Set a connect message to the mqtt broker
    connmsg.set_connect_proto_version(4)  # Set protocol version to MQTT version 3.11
    connmsg.set_connect_client_id(mqtt_client_id)
    connmsg.set_connect_username("admin")  # TODO: set Kubernetes secrets for mqtt
    connmsg.set_connect_password("public")
    connmsg.set_connect_keep_alive(60)
    connmsg.set_connect_clean_session(True)
    return connmsg

def build_pub_message(mqtt_min_message_size, mqtt_max_message_size, topic):
    pubmsg = pynng.Mqttmsg()
    pubmsg.set_packet_type(PUB)  # Set a pub message to the mqtt broker
    pubmsg.set_publish_topic(topic)
    pubmsg.set_publish_qos(mqtt_qos)
    payload = build_payload(mqtt_min_message_size, mqtt_max_message_size)
    pubmsg.set_publish_payload(payload, len(payload))
    return pubmsg

async def main():
    logging.info(mqtt_client_id)
    logging.info("waiting for: " + str(delay * int(mqtt_client_id.split("-")[5])))
    await asyncio.sleep(delay * int(mqtt_client_id.split("-")[5]))

    address = ("mqtt-quic://" + mqtt_cluster_ip + ":" + mqtt_cluster_port)  # build address:port
    topic = build_topic(mqtt_topic, mqtt_client_id)

    last_index = 0  # Track the last index of the published message

    while True:
        try:
            with pynng.Mqtt_quic(address) as mqtt:
                logging.info("Connecting to: " + address + " with topic: " + topic)
                connmsg = build_conn_message(mqtt_secrets)
                await mqtt.asend_msg(connmsg)

                # Start publishing messages from the last index
                for i in range(last_index, mqtt_message_num):  # Start from the last published index
                    logging.info(f"Sending message {i}")
                    pubmsg = build_pub_message(mqtt_min_message_size, mqtt_max_message_size, topic)  # build a MQTT message
                    await mqtt.asend_msg(pubmsg)
                    last_index = i + 1  # Update the last index after sending
                    await asyncio.sleep(mqtt_message_freq_ms)  # converting time delay to ms

                logging.info(f"Done. at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except pynng.exceptions.NNGException as e:
            logging.error(f"Connection error: {e}. Attempting to reconnect...")
            await asyncio.sleep(5)  # Wait before retrying the connection

            # Attempt to reconnect and resume publishing
            while True:
                try:
                    with pynng.Mqtt_quic(address) as mqtt:
                        logging.info("Reconnecting to: " + address + " with topic: " + topic)
                        connmsg = build_conn_message(mqtt_secrets)
                        await mqtt.asend_msg(connmsg)

                        # Resume publishing from the last index
                        for i in range(last_index, mqtt_message_num):
                            logging.info(f"Resuming message {i}")
                            pubmsg = build_pub_message(mqtt_min_message_size, mqtt_max_message_size, topic)
                            await mqtt.asend_msg(pubmsg)
                            last_index = i + 1  # Update the last index after sending
                            await asyncio.sleep(mqtt_message_freq_ms)

                        break  # Exit the reconnection loop if successful

                except pynng.exceptions.NNGException:
                    logging.error("Reconnection failed. Retrying...")
                    await asyncio.sleep(5)  # Wait before retrying the reconnection

if __name__ == "__main__":
    logging.info("Starting Version 1.0.5")
    try:
        asyncio.run(main())
    except pynng.exceptions.NNGException:
        logging.info("Connection closed")
    except KeyboardInterrupt:
        exit(0)