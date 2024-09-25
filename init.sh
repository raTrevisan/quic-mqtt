#!/bin/sh
cd ./pynng-mqtt/nng/extern/msquic
mkdir -p build
cd build
cmake ..
make -j8
# install if build successfully
sudo make install