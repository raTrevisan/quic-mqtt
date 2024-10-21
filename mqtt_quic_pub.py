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

CONN = 1
PUB = 3
SUB = 8

mqtt_cluster_ip = os.getenv("MQTT_CLUSTER_IP")
mqtt_cluster_port = os.getenv("MQTT_CLUSTER_PORT")
mqtt_topic= os.getenv("MQTT_TOPIC")
mqtt_qos = os.getenv("MQTT_QOS")
mqtt_secrets = os.getenv("MQTT_SECRETS")
mqtt_message_num = os.getenv("MQTT_MESSAGE_NUM")
mqtt_message_size = os.getenv("MQTT_MESSAGE_SIZE")
mqtt_message_freq_ms = os.getenv("MQTT_MESSAGE_FREQ_MS")


def build_payload(mqtt_message_size):
  payload = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(mqtt_message_size)) # creates a random string thats 'mqtt_message_size' long
  return payload


def build_conn_message(mqtt_secrets):
  connmsg = pynng.Mqttmsg()
  connmsg.set_packet_type(CONN) #Set a connect message to the mqtt broker
  connmsg.set_connect_proto_version(4) #Set protocol version to MQTT version 3.11
  connmsg.set_connect_username("admin") #TODO set kubenrnetes secrets for mqtt
  connmsg.set_connect_password("public")
  connmsg.set_connect_keep_alive(60)
  connmsg.set_connect_clean_session(True)
  return connmsg


def build_pub_message(mqtt_message_size):
  pubmsg = pynng.Mqttmsg()
  pubmsg.set_packet_type(PUB) #Set a pub message to the mqtt broker
  pubmsg.set_publish_topic(mqtt_topic)
  pubmsg.set_publish_qos(int(mqtt_qos))
  payload = build_payload(mqtt_message_size)
  pubmsg.set_publish_payload(payload, len(payload))
  return pubmsg


async def main():
  address = (mqtt_cluster_ip + ":" + mqtt_cluster_port) # build address:port
  build_conn_message(mqtt_secrets)

  with pynng.Mqtt_quic(address) as mqtt:

    print("Connecting to : " + address)
    connmsg = build_conn_message(mqtt_secrets)
    await mqtt.asend_msg(connmsg)
    print(f"Connect packet sent.")



    for i in range(mqtt_message_num): # sending 'mqtt_message_num' messages
        pubmsg = build_pub_message(mqtt_message_size) #build a MQTT message
        await mqtt.asend_msg(pubmsg)
        await asyncio.sleep(float(mqtt_message_freq_ms)/1000) #converting time delay to ms
    
    print(f"Done.")

if __name__ == "__main__":
  try:
    asyncio.run(main())
  except pynng.exceptions.NNGException:
    print("Connection closed")
  except KeyboardInterrupt:
    # that's the way the program *should* end
    exit(0)
