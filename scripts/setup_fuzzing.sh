#!/bin/bash
sudo apt update
sudo apt install -y afl++ clang gdb python3-pip
pip install angr pwntools
docker build -t hunter-fuzzer:latest -f Dockerfile.fuzzer .