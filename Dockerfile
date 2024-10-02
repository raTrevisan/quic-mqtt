FROM debian:10
RUN su
RUN apt update
# Installing msquic https://github.com/microsoft/msquic/blob/main/docs/BUILD.md
RUN apt-get install software-properties-common -y
RUN apt update
RUN apt install wget -y
RUN wget -q https://packages.microsoft.com/config/ubuntu/18.04/packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN apt-get update
RUN sed -i "/^# deb.*universe/ s/^# //" /etc/apt/sources.list
RUN apt-get install -y powershell
RUN pwsh
#RUN apt purge wget -y
#installing cmake ver 3.15.0
RUN apt install build-essential -y
RUN apt-get install git -y
RUN apt install ninja-build -y
RUN mkdir build
WORKDIR /build
RUN wget https://github.com/Kitware/CMake/releases/download/v3.15.3/cmake-3.15.3.tar.gz
RUN tar zxvf cmake-3.15.3.tar.gz
RUN cmake-3.15.3/bootstrap
RUN make
RUN make install
#installing NanoSDK
WORKDIR /
RUN git clone https://github.com/nanomq/NanoSDK.git
WORKDIR /NanoSDK
RUN git submodule update --init --recursive
RUN mkdir ./build
WORKDIR /NanoSDK/build 
RUN cmake -G Ninja ..
RUN ninja



#COPY ./pynng-mqtt ./pynng-mqtt
#COPY ./init.sh ./init.sh
#RUN sed 's/\r//g' ./init.sh > ./init.sh
#RUN ./init.sh
#ENTRYPOINT ["python3", "pynng-mqtt/examples/mqtt_quic_sub.py", "topic", "1"]