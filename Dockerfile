FROM alpine:3.14
RUN apk update
RUN apk add \
    linux-headers \
    perl \
    alpine-sdk \
    make \
    cmake \
    python3-dev \
    nano \
    sudo \
    git \
    numactl-dev \
    py3-pip \
    lttng-ust-dev \
    musl-dev \
    openssl-dev &&\
    cd /tmp && git clone --depth 1 --single-branch --branch main --recursive https://github.com/dotnet/msquic && \
    cd msquic/src/msquic && cmake -B build/linux/arm64_openssl -DQUIC_OUTPUT_DIR=/tmp/msquic/src/msquic/artifacts/bin/linux/arm64_Release_openssl        -DCMAKE_BUILD_TYPE=Release        -DCMAKE_TARGET_ARCHITECTURE=arm64        -DQUIC_TLS=openssl        -DQUIC_ENABLE_LOGGING=true        -DQUIC_USE_SYSTEM_LIBCRYPTO=true        -DQUIC_BUILD_TOOLS=off        -DQUIC_BUILD_TEST=off        -DQUIC_BUILD_PERF=off && \
    cmake --build build/linux/arm64_openssl  --config Release && \     
    cp artifacts/bin/linux/arm64_Release_openssl/libmsquic.so.* artifacts/bin/linux/arm64_Release_openssl/libmsquic.lttng.so.* /usr/lib && \    
    rm -rf /tmp/msquic && \     
    apk del git lttng-ust-dev musl-dev openssl-dev && \
    cd /
    
COPY ./pynng-mqtt ./pynng-mqtt
COPY ./init.sh ./init.sh
RUN sed 's/\r//g' ./init.sh > ./init.sh
RUN ./init.sh
#ENTRYPOINT ["python3", "pynng-mqtt/examples/mqtt_quic_sub.py", "topic", "1"]