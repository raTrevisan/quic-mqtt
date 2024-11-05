"""
MQTT_CLUSTER_IP => String, IP address of the MQTT broker
MQTT_CLUSTER_PORT => Int, port of the MQTT broker, quic default is 14567
MQTT_TOPIC => String topic in which messages will be sent. Can have multiple levels and use wildcards (+, #)
MQTT_QOS => [0,1,2], MQTT Quality of service
MQTT_SECRETS => kubernetes secret Username and password
"""


import pynng
import os
import asyncio
import logging
import datetime


# MQTT packet type constants
# CONN: Connection request packet type
# PUB: Publish message packet type
# SUB: Subscribe request packet type
CONN = 1
PUB = 3
SUB = 8

mqtt_cluster_ip = os.getenv("MQTT_CLUSTER_IP")
mqtt_cluster_port = os.getenv("MQTT_CLUSTER_PORT")
mqtt_topic= os.getenv("MQTT_TOPIC")
mqtt_qos = os.getenv("MQTT_QOS")
mqtt_secrets = os.getenv("MQTT_SECRETS")
mqtt_client_id = os.getenv("POD_NAME")

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

def build_conn_message(mqtt_secrets):
  #logging.info("Building connection Message ")
  connmsg = pynng.Mqttmsg()
  connmsg.set_packet_type(CONN) #Set a connect message to the mqtt broker
  connmsg.set_connect_client_id(mqtt_client_id)
  connmsg.set_connect_proto_version(4) #Set protocol version to MQTT version 3.11
  connmsg.set_connect_username("admin") #TODO set kubenrnetes secrets for mqtt
  connmsg.set_connect_password("public")
  connmsg.set_connect_keep_alive(10)
  connmsg.set_connect_clean_session(True)
  return connmsg


def build_sub_message(mqtt_topic, mqtt_qos):
  #logging.info("Building subscribe Message ")
  submsg = pynng.Mqttmsg()
  submsg.set_packet_type(SUB) #Set a pub message to the mqtt broker
  submsg.set_subscribe_topic(mqtt_topic, len(mqtt_topic), int(mqtt_qos), 0, 0, 0)
  return submsg


async def main():
  address = ("mqtt-quic://" + mqtt_cluster_ip + ":" + mqtt_cluster_port) # build address:port
  logging.info("Connecting to cluster at: " + address)

  with pynng.Mqtt_quic(address) as mqtt:
    connmsg = build_conn_message(mqtt_secrets)
    await mqtt.asend_msg(connmsg)
    #logging.info("Connect packet sent.")

    #logging.info("Subscribing to topic : " + mqtt_topic)
    submsg = build_sub_message(mqtt_topic, mqtt_qos)
    #logging.info("Subscribe message sent")
    await mqtt.asend_msg(submsg)
    logging.info("Subscribed to topic: " + mqtt_topic)
    while True:
      rmsg = await mqtt.arecv_msg()
      rmsg.__class__ = pynng.Mqttmsg # convert to mqttmsg
      if rmsg.packet_type() == 3:
        logging.info("Message received on topic: " + str(rmsg.publish_topic()) + 
                     " with payload size: " + str(len(rmsg.publish_payload())) + 
                       " at " + str(datetime.datetime.now()))
      else:
        logging.info("Unhandled packet type received")

if __name__ == "__main__":
  logging.info("Starting Version 1.0.1")
  try:
    asyncio.run(main())
  except pynng.exceptions.NNGException:
    logging.info("Connection closed")
  except KeyboardInterrupt:   # that's the way the program *should* end
    exit(0)
  