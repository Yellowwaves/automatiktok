#!/bin/bash

# Update the package list
sudo apt update -y
sudo apt-get install libnet1
sudo apt install -y libdnet-dev make unzip autoconf gcc g++ pkg-config
sudo apt install -y autoconf
sudo apt install -y g++
sudo apt install -y unzip


# Install dependencies for Snort 3
sudo apt install -y build-essential libpcap-dev libpcre3-dev libnet1-dev zlib1g-dev luajit hwloc libdnet-dev libdumbnet-dev bison flex liblzma-dev openssl libssl-dev pkg-config libhwloc-dev cmake cpputest libsqlite3-dev uuid-dev libcmocka-dev libnetfilter-queue-dev libmnl-dev autotools-dev libluajit-5.1-dev libunwind-dev libfl-dev

# Create a directory to store source files
mkdir -p ~/snort_src && cd ~/snort_src

# Install Snort DAQ (Data Acquisition library) from source
git clone https://github.com/snort3/libdaq.git
cd libdaq
./bootstrap
./configure
make
sudo make install

# Download and install Google's Tcmalloc (optional but recommended)
cd ../
wget https://github.com/gperftools/gperftools/releases/download/gperftools-2.9.1/gperftools-2.9.1.tar.gz
tar xzf gperftools-2.9.1.tar.gz
cd gperftools-2.9.1/
./configure
make
sudo make install

# Download and install Snort 3 from the source
cd ../
wget https://github.com/snort3/snort3/archive/refs/heads/master.zip
unzip master.zip
cd snort3-master

# Configure Snort 3 with Tcmalloc enabled
./configure_cmake.sh --prefix=/usr/local --enable-tcmalloc

# Optional: list available features to enable extra capabilities (e.g., large PCAP support)
# ./configure_cmake.sh --help

echo "Snort 3 installation and configuration completed successfully."
