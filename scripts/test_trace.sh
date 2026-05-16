#!/bin/bash
set -e

TRACEPARENT_1=$(curl -s -D - http://localhost:8000/stickers -o /dev/null | grep -i traceparent | tr -d '\r')
TRACE_ID_1=$(echo "$TRACEPARENT_1" | cut -d'-' -f2)

TRACEPARENT_2=$(curl -s -D - http://localhost:8000/stickers/1 -o /dev/null | grep -i traceparent | tr -d '\r')
TRACE_ID_2=$(echo "$TRACEPARENT_2" | cut -d'-' -f2)

echo "[sticker-api] trace_id from GET /stickers:   $TRACE_ID_1"
echo "[sticker-api] trace_id from GET /stickers/1: $TRACE_ID_2"

echo ""
echo "[sticker-api] otel-collector metrics (first 20 lines):"
curl -s http://localhost:8888/metrics | head -20
