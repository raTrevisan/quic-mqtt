FROM debian:10
RUN su
RUN apt update
RUN apt-get install software-properties-common -y
RUN apt update
RUN apt-get install libssl-dev
RUN apt install build-essential -y
RUN apt-get install git -y
RUN apt install ninja-build -y
RUN apt install wget -y
RUN apt install libffi-dev -y
RUN apt install libmbedtls-dev libmbedtls12 -y
RUN mkdir build
WORKDIR /build
RUN wget https://github.com/Kitware/CMake/releases/download/v3.30.4/cmake-3.30.4.tar.gz
RUN tar zxvf cmake-3.30.4.tar.gz
RUN cmake-3.30.4/bootstrap
RUN make
RUN make install
WORKDIR /
RUN git clone https://github.com/wanghaEMQ/pynng-mqtt.git
RUN cd pynng-mqtt && git submodule update --init --recursive
RUN apt install python3-dev -y
RUN apt-get install python3-pip -y
COPY ./pynng-mqtt/pyproject.toml ./pynng-mqtt/pyproject.toml
WORKDIR /pynng-mqtt/nng/extern/msquic
RUN mkdir -p build
WORKDIR /pynng-mqtt/nng/extern/msquic/build
RUN cmake ..
RUN make -j8
RUN make install
WORKDIR /pynng-mqtt
RUN pip3 install --user asyncio 
RUN pip3 install .
RUN ldconfig
WORKDIR /pynng-mqtt/examples
ENTRYPOINT ["python3", "mqtt_quic_sub.py", "topic", "1"]