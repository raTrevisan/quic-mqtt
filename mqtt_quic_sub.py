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

CONN = 1
PUB = 3
SUB = 8

mqtt_cluster_ip = os.getenv("MQTT_CLUSTER_IP")
mqtt_cluster_port = os.getenv("MQTT_CLUSTER_PORT")
mqtt_topic= os.getenv("MQTT_TOPIC")
mqtt_qos = os.getenv("MQTT_QOS")
mqtt_secrets = os.getenv("MQTT_SECRETS")


def build_conn_message(mqtt_secrets):
  print("Building connection Message ")
  connmsg = pynng.Mqttmsg()
  connmsg.set_packet_type(CONN) #Set a connect message to the mqtt broker
  connmsg.set_connect_proto_version(4) #Set protocol version to MQTT version 3.11
  connmsg.set_connect_username("admin") #TODO set kubenrnetes secrets for mqtt
  connmsg.set_connect_password("public")
  connmsg.set_connect_keep_alive(60)
  connmsg.set_connect_clean_session(True)
  return connmsg


def build_sub_message(mqtt_topic, mqtt_qos):
  print("Building subscribe Message ")
  submsg = pynng.Mqttmsg()
  submsg.set_packet_type(SUB) #Set a pub message to the mqtt broker
  submsg.set_subscribe_topic(mqtt_topic, len(mqtt_topic), int(mqtt_qos), 0, 0, 0)
  return submsg


async def main():
  address = (mqtt_cluster_ip + ":" + mqtt_cluster_port) # build address:port
  print("Connecting to : " + address)

  with pynng.Mqtt_quic(address) as mqtt:
    connmsg = build_conn_message(mqtt_secrets)
    print("Connect packet sent.")
    await mqtt.asend_msg(connmsg)

    print("Subscribing to topic : " + mqtt_topic)
    submsg = build_sub_message(mqtt_topic, mqtt_qos)
    print("Subscribe message sent")
    await mqtt.asend_msg(submsg)
    while True:
      rmsg = await mqtt.arecv_msg()
      rmsg.__class__ = pynng.Mqttmsg # convert to mqttmsg
      print("msg", rmsg, "arrived.")
      print("type:   ", rmsg.packet_type())
      print("qos:    ", rmsg.publish_qos())
      print("topic:  ", rmsg.publish_topic())
      print("payload:", rmsg.publish_payload(), "(", rmsg.publish_payload_sz(), ")")


    print(f"Done.")

if __name__ == "__main__":
  print("Starting")
  try:
    asyncio.run(main())
  except pynng.exceptions.NNGException:
    print("Connection closed")
  except KeyboardInterrupt:
    # that's the way the program *should* end
    exit(0)