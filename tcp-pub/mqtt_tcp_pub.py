"""
MQTT is used for synchronous communications where each question is responded with a single answer,
for example remote procedure calls (RPCs).
Like Pipeline, it also can perform load-balancing.
This is the only reliable messaging pattern in the suite, as it automatically will retry if a request is not matched with a response.

"""
import sys
import pynng
import asyncio

helper = "Usage:\n\tmqttpub.py <topic> <qos> <payload>"

address = "mqtt-tcp://emqx.dtwins:1883"

async def main():
  with pynng.Mqtt_tcp(address) as mqtt:
    print(f"Make a connect msg")
    connmsg = pynng.Mqttmsg()
    connmsg.set_packet_type(1) # 0x01 Connect
    connmsg.set_connect_proto_version(4) # MqttV311
    mqtt.dial_msg(address, connmsg)
    print(f"Connection packet sent.")
    pubmsg = pynng.Mqttmsg()
    pubmsg.set_packet_type(3) # 0x03 Publish
    message = "tcp message"
    pubmsg.set_publish_payload(message, len(message))
    pubmsg.set_publish_topic("test")
    pubmsg.set_publish_qos(0)
    await mqtt.asend_msg(pubmsg)
    print(f"Publish packet sent.")

if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    # that's the way the program *should* end
    exit(0)