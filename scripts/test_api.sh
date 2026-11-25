#!/usr/bin/env bash
# Calls every endpoint of the deployed API and checks the status codes.
# Output is shown on screen and saved to evidence/ for the submission.
#
# Usage (AWS CloudShell or any bash with curl):
#   export API_URL="https://<api-id>.execute-api.<region>.amazonaws.com/dev"
#   export API_KEY="<your API key>"      # never commit this value
#   bash scripts/test_api.sh
set -uo pipefail

: "${API_URL:?set API_URL to the stage invoke URL, e.g. https://abc123.execute-api.us-east-1.amazonaws.com/dev}"
: "${API_KEY:?set API_KEY to the API key value}"
API_URL="${API_URL%/}"

mkdir -p evidence
OUT="evidence/curl_outputs_$(date -u +%Y%m%dT%H%M%SZ).txt"
PASS=0
FAIL=0

# call <expected status> <method> <path> [json body] [key|nokey]
call() {
  local expected="$1" method="$2" path="$3" body="${4:-}" auth="${5:-key}"
  local args=(-s -o /tmp/body.$$ -w '%{http_code}' -X "$method" "$API_URL$path")
  [ "$auth" = key ] && args+=(-H "x-api-key: $API_KEY")
  [ -n "$body" ] && args+=(-H "Content-Type: application/json" -d "$body")

  STATUS=$(curl "${args[@]}")
  BODY=$(cat /tmp/body.$$ 2>/dev/null)
  local result="PASS"
  if [ "$STATUS" = "$expected" ]; then PASS=$((PASS + 1)); else result="FAIL"; FAIL=$((FAIL + 1)); fi

  echo "\$ curl -X $method $path$([ "$auth" = key ] && echo ' -H "x-api-key: ****"')${body:+ -d '$body'}"
  echo "HTTP $STATUS (expected $expected) $result"
  echo "${BODY:-<no body>}"
  echo
}

{
  echo "API test run: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Host: ${API_URL#https://}" | sed -E 's/^[a-z0-9]+\./<api-id>./'
  echo

  echo "== Create =="
  call 201 POST /items '{"name":"Rice 5kg","quantity":12,"unit":"bag","reorderLevel":3}'
  ITEM_ID=$(printf '%s' "$BODY" | sed -n 's/.*"itemId": *"\([^"]*\)".*/\1/p')
  [ -n "$ITEM_ID" ] || ITEM_ID="missing-item-id"

  echo "== Read =="
  call 200 GET "/items/$ITEM_ID"

  echo "== Update =="
  call 200 PUT "/items/$ITEM_ID" '{"name":"Rice 5kg","quantity":2,"unit":"bag","reorderLevel":3}'

  echo "== Delete =="
  call 204 DELETE "/items/$ITEM_ID"

  echo "== Read after delete =="
  call 404 GET "/items/$ITEM_ID"

  echo "== Validation: negative quantity =="
  call 400 POST /items '{"name":"Sugar","quantity":-1,"unit":"kg","reorderLevel":2}'

  echo "== Security: request without API key =="
  call 403 GET "/items/$ITEM_ID" "" nokey

  echo "Result: $PASS passed, $FAIL failed"
} | tee "$OUT"

rm -f /tmp/body.$$
echo "Saved to $OUT"
grep -q "Result: .* 0 failed" "$OUT"
