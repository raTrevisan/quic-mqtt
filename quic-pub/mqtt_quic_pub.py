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

mqtt_cluster_ip = os.getenv("MQTT_CLUSTER_IP")
mqtt_cluster_port = os.getenv("MQTT_CLUSTER_PORT")
mqtt_topic= os.getenv("MQTT_TOPIC")
mqtt_qos = int(os.getenv("MQTT_QOS"))
mqtt_secrets = os.getenv("MQTT_SECRETS")
mqtt_message_num = int(os.getenv("MQTT_MESSAGE_NUM"))
mqtt_message_size = int(os.getenv("MQTT_MESSAGE_SIZE"))
mqtt_message_freq_ms = int(os.getenv("MQTT_MESSAGE_FREQ_MS"))/1000
mqtt_client_id = os.getenv("POD_NAME")


def build_payload(mqtt_message_size):
  time = datetime.datetime.now()
  payload = (''.join(random.choice(string.ascii_uppercase + string.digits) 
                     for _ in range(mqtt_message_size)) + "#" + str(time)) # creates a random string thats 'mqtt_message_size' long
  return payload


def build_conn_message(mqtt_secrets):
  connmsg = pynng.Mqttmsg()
  connmsg.set_packet_type(CONN) #Set a connect message to the mqtt broker
  connmsg.set_connect_proto_version(4) #Set protocol version to MQTT version 3.11
  connmsg.set_connect_client_id(mqtt_client_id)
  connmsg.set_connect_username("admin") #TODO set kubenrnetes secrets for mqtt
  connmsg.set_connect_password("public")
  connmsg.set_connect_keep_alive(60)
  connmsg.set_connect_clean_session(True)
  return connmsg


def build_pub_message(mqtt_message_size):
  pubmsg = pynng.Mqttmsg()
  pubmsg.set_packet_type(PUB) #Set a pub message to the mqtt broker
  pubmsg.set_publish_topic(mqtt_topic)
  pubmsg.set_publish_qos(mqtt_qos)
  payload = build_payload(mqtt_message_size)
  pubmsg.set_publish_payload(payload, len(payload))
  return pubmsg


async def main():
  address = ("mqtt-quic://" + mqtt_cluster_ip + ":" + mqtt_cluster_port) # build address:port
  build_conn_message(mqtt_secrets)

  with pynng.Mqtt_quic(address) as mqtt:

    logging.info("Connecting to : " + address)
    connmsg = build_conn_message(mqtt_secrets)
    await mqtt.asend_msg(connmsg)


    for i in range(mqtt_message_num): # sending 'mqtt_message_num' messages
        logging.info(f"Sending message {i}")
        pubmsg = build_pub_message(mqtt_message_size) #build a MQTT message
        await mqtt.asend_msg(pubmsg)
        await asyncio.sleep(mqtt_message_freq_ms) #converting time delay to ms
    
    logging.info(f"Done. at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
      await asyncio.sleep(1)

if __name__ == "__main__":
  logging.info("Starting Version 1.0.0")
  try:
    asyncio.run(main())
  except pynng.exceptions.NNGException:
    logging.info("Connection closed")
  except KeyboardInterrupt:
    # that's the way the program *should* end
    exit(0)
