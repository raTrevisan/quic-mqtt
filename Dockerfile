FROM alpine:3.14
RUN apk update
RUN apk add \
    linux-headers \
    perl \
    alpine-sdk \
    make \
    cmake \
    python3-dev \
    curl \
    nano \
    sudo \
    git
COPY ./pynng-mqtt ./pynng-mqtt
COPY ./init.sh ./init.sh
RUN ./init.sh
