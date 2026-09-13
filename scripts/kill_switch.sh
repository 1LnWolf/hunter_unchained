#!/bin/bash
pkill -f hunter
docker kill $(docker ps -q --filter "label=hunter")
rm -rf /tmp/fuzz_out /tmp/payload