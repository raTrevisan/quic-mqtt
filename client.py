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

address = "mqtt-quic://127.0.0.1:14567"

async def main():
  with pynng.Mqtt_quic(address) as mqtt:
    print(f"Make a connect msg")
    connmsg = pynng.Mqttmsg()
    connmsg.set_packet_type(1) # 0x01 Connect
    connmsg.set_connect_proto_version(4) # MqttV311
    connmsg.set_connect_username("alvin")
    connmsg.set_connect_password("alvin123")
    await mqtt.asend_msg(connmsg)
    print(f"Connect packet sent.")
    for i in range(20):
        pubmsg = pynng.Mqttmsg()
        pubmsg.set_packet_type(3) # 0x03 Publish
        pubmsg.set_publish_topic(sys.argv[1])
        pubmsg.set_publish_qos(int(sys.argv[2]))
        pld = sys.argv[3]
        for j in range(i-1):
            pld += pld
        pubmsg.set_publish_payload(pld, len(pld))
        await mqtt.asend_msg(pubmsg)
        print(f"Publish packet sent.", len(pld))
        await asyncio.sleep(0.5)

if __name__ == "__main__":
  if len(sys.argv) != 4:
    print(helper)
    exit(0)
  try:
    asyncio.run(main())
  except pynng.exceptions.NNGException:
    print("Connection closed")
  except KeyboardInterrupt:
    # that's the way the program *should* end
    exit(0)