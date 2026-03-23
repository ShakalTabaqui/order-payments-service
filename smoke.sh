#!/usr/bin/env bash
set -euo pipefail

PORT="${API_PORT:-8000}"

usage() {
  cat <<'EOF'
Linux smoke test for the payments service.

Usage:
  ./smoke.sh [--port 8001]

Env:
  API_PORT (optional)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

export API_PORT="${PORT}"
docker compose up -d --build

base="http://localhost:${PORT}"

for i in $(seq 1 60); do
  if curl -fsS "${base}/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "${i}" -eq 60 ]]; then
    echo "API did not become healthy on ${base}" >&2
    exit 1
  fi
  sleep 1
done

orders_json="$(curl -fsS "${base}/orders")"
echo "${orders_json}" | grep -q '"id"' || {
  echo "Expected /orders to return data" >&2
  exit 1
}

order_id="$(
  echo "${orders_json}" |
    sed -n \
      's/.*"id"[[:space:]]*:[[:space:]]*\\([0-9][0-9]*\\).*/\\1/p' |
    head -n1
)"
if [[ -z "${order_id}" ]]; then
  echo "Failed to extract order id" >&2
  exit 1
fi

payment_json="$(
  curl -fsS -X POST "${base}/orders/${order_id}/payments" \
    -H "Content-Type: application/json" \
    -d '{"amount":"100.00","payment_type":"cash"}'
)"
echo "${payment_json}" | grep -q '"status"' || {
  echo "Expected payment to be created" >&2
  exit 1
}

payment_id="$(
  echo "${payment_json}" |
    sed -n \
      's/.*"id"[[:space:]]*:[[:space:]]*\\([0-9][0-9]*\\).*/\\1/p' |
    head -n1
)"
if [[ -z "${payment_id}" ]]; then
  echo "Failed to extract payment id" >&2
  exit 1
fi

curl -fsS -X POST "${base}/payments/${payment_id}/refund" >/dev/null

echo "SMOKE OK"
