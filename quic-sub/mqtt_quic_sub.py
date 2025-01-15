import pynng
import os
import asyncio
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
mqtt_client_id = os.getenv("POD_NAME")

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

def build_sub_message(sub_topic, mqtt_qos):
    submsg = pynng.Mqttmsg()
    submsg.set_packet_type(SUB)  # Set a subscribe message to the mqtt broker
    submsg.set_subscribe_topic(sub_topic, len(sub_topic), int(mqtt_qos), 0, 0, 0)
    return submsg

async def main():
    logging.info(mqtt_client_id)
    logging.info("waiting for: " + str(delay * int(mqtt_client_id.split("-")[5])))
    await asyncio.sleep(delay * int(mqtt_client_id.split("-")[5]))

    address = ("mqtt-quic://" + mqtt_cluster_ip + ":" + mqtt_cluster_port)  # build address:port
    topic = mqtt_topic  # Assuming you have a way to build the topic

    while True:
        try:
            with pynng.Mqtt_quic(address) as mqtt:
                logging.info("Connecting to: " + address + " with topic: " + topic)
                connmsg = build_conn_message(mqtt_secrets)
                await mqtt.asend_msg(connmsg)

                # Subscribe to the topic
                submsg = build_sub_message(topic, mqtt_qos)
                await mqtt.asend_msg(submsg)
                logging.info(f"Subscribed to topic: {topic}")

                while True:
                    rmsg = await mqtt.arecv_msg()
                    rmsg.__class__ = pynng.Mqttmsg  # Convert to mqttmsg
                    if rmsg.packet_type() == PUB:
                        logging.info("Message received on topic: " + str(rmsg.publish_topic()) +
                                     " with payload size: " + str(len(rmsg.publish_payload())) +
                                     " at " + str(datetime.datetime.now()) +
                                     " sent " + str(rmsg.publish_payload()).split("#")[1])
                    else:
                        logging.info("Unhandled packet type received")

        except pynng.exceptions.NNGException as e:
            logging.error(f"Connection error: {e}. Attempting to reconnect...")
            await asyncio.sleep(5)  # Wait before retrying the connection

            # Attempt to reconnect and resume subscribing
            while True:
                try:
                    with pynng.Mqtt_quic(address) as mqtt:
                        logging.info("Reconnecting to: " + address + " with topic: " + topic)
                        connmsg = build_conn_message(mqtt_secrets)
                        await mqtt.asend_msg(connmsg)

                        # Re-subscribe to the topic
                        submsg = build_sub_message(topic, mqtt_qos)
                        await mqtt.asend_msg(submsg)
                        logging.info(f"Re-subscribed to topic: {topic}")

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