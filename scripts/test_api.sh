#!/usr/bin/env bash
# Calls every endpoint of the deployed API and checks the status codes.
# Output is shown on screen and saved to evidence/ for the submission.
#
# Usage (Git Bash on your laptop, or the EC2 instance):
#   export API_URL="http://<EC2 public IP>"     # or http://localhost when testing locally
#   bash scripts/test_api.sh
set -uo pipefail

: "${API_URL:?set API_URL to the API address, e.g. http://203.0.113.10}"
API_URL="${API_URL%/}"

mkdir -p evidence
OUT="evidence/curl_outputs_$(date -u +%Y%m%dT%H%M%SZ).txt"
PASS=0
FAIL=0

# call <expected status> <method> <path> [json body]
call() {
  local expected="$1" method="$2" path="$3" body="${4:-}"
  local args=(-s -o /tmp/body.$$ -w '%{http_code}' -X "$method" "$API_URL$path")
  [ -n "$body" ] && args+=(-H "Content-Type: application/json" -d "$body")

  STATUS=$(curl "${args[@]}")
  BODY=$(cat /tmp/body.$$ 2>/dev/null)
  local result="PASS"
  if [ "$STATUS" = "$expected" ]; then PASS=$((PASS + 1)); else result="FAIL"; FAIL=$((FAIL + 1)); fi

  echo "\$ curl -X $method $path${body:+ -d '$body'}"
  echo "HTTP $STATUS (expected $expected) $result"
  echo "${BODY:0:300}"; [ -n "$BODY" ] || echo "<no body>"
  echo
}

{
  echo "API test run: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Host: $API_URL"
  echo

  echo "== Connectivity: health check =="
  call 200 GET /health

  echo "== Create =="
  call 201 POST /items '{"name":"Rice 5kg","quantity":12,"unit":"bag","reorderLevel":3}'
  ITEM_ID=$(printf '%s' "$BODY" | sed -n 's/.*"itemId": *"\([^"]*\)".*/\1/p')
  [ -n "$ITEM_ID" ] || ITEM_ID="missing-item-id"

  echo "== List (low stock only) =="
  call 200 GET "/items?lowStock=true"

  echo "== Web page =="
  call 200 GET /

  echo "== Read =="
  call 200 GET "/items/$ITEM_ID"

  echo "== Update =="
  call 200 PUT "/items/$ITEM_ID" '{"name":"Rice 5kg","quantity":2,"unit":"bag","reorderLevel":3}'

  echo "== Update with unchanged values =="
  call 200 PUT "/items/$ITEM_ID" '{"name":"Rice 5kg","quantity":2,"unit":"bag","reorderLevel":3}'

  echo "== Delete =="
  call 204 DELETE "/items/$ITEM_ID"

  echo "== Read after delete =="
  call 404 GET "/items/$ITEM_ID"

  echo "== Validation: negative quantity =="
  call 400 POST /items '{"name":"Sugar","quantity":-1,"unit":"kg","reorderLevel":2}'

  echo "== Update unknown item =="
  call 404 PUT /items/does-not-exist '{"name":"Sugar","quantity":1,"unit":"kg","reorderLevel":2}'

  echo "Result: $PASS passed, $FAIL failed"
} | tee "$OUT"

rm -f /tmp/body.$$
echo "Saved to $OUT"
grep -q "Result: .* 0 failed" "$OUT"
