#!/usr/bin/env bash
# Open an SSH tunnel so localhost:9092 is the course Kafka broker.
# Leave this terminal running. It will not print anything after you log in.
#
# Off campus: connect to CMU VPN first.
# Password for user "tunnel": mlip-kafka

set -euo pipefail
exec ssh -o ServerAliveInterval=60 -L 9092:localhost:9092 tunnel@128.2.220.123 -NT
