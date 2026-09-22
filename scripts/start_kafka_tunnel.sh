#!/usr/bin/env bash
# Forward course Kafka (localhost:9092 on the CMU server) to this machine.
# Leave this running in the background while you collect data.
set -euo pipefail

HOST="${KAFKA_SERVER_IP:-128.2.220.123}"
USER="${SSH_TUNNEL_USER:-tunnel}"
PORT="${KAFKA_LOCAL_PORT:-9092}"

echo "Starting SSH tunnel: localhost:${PORT} -> ${USER}@${HOST}:9092"
echo "This process prints nothing on success. Stop it with Ctrl+C."
echo "If ssh asks for a password, use the course tunnel password from Canvas."
exec ssh \
  -o StrictHostKeyChecking=accept-new \
  -o ServerAliveInterval=30 \
  -o ExitOnForwardFailure=yes \
  -L "${PORT}:localhost:9092" \
  "${USER}@${HOST}" \
  -NT
