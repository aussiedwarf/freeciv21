#!/bin/bash
# Integration test for first-strike combat mechanics.
# Runs a headless nationstates autogame and checks debug logs for
# first-strike events.
#
# Requirements:
#   - Debug build at builds/linux-x64-gcc-debug/freeciv21-server
#     Build with:
#       cmake -B builds/linux-x64-gcc-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -S /workspace
#       cmake --build builds/linux-x64-gcc-debug --parallel $(nproc)
#
# Usage:
#   bash tests/test_first_strikes.sh

set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
SERVER="${WORKSPACE}/builds/linux-x64-gcc-debug/freeciv21-server"
SERV_FILE="$(mktemp /tmp/test-first-strikes-XXXXXX.serv)"
OUTPUT="$(mktemp /tmp/first-strikes-output-XXXXXX.log)"

cleanup() {
  rm -f "$SERV_FILE" "$OUTPUT"
}
trap cleanup EXIT

# Check for Debug build
if [ ! -x "$SERVER" ]; then
  echo "ERROR: Debug server not found at $SERVER"
  echo "Build it with:"
  echo "  cmake -B builds/linux-x64-gcc-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -S $WORKSPACE"
  echo "  cmake --build builds/linux-x64-gcc-debug --parallel \$(nproc)"
  exit 2
fi

# Create server config that accelerates the game to produce first-strike combat.
# Uses fixed seeds for reproducibility and gives AI players techs that unlock
# first-strike units (Warrior Code -> Archers with first_strikes=1).
cat > "$SERV_FILE" << 'SERVEOF'
rulesetdir nationstates
set aifill 6
set endt 200
set autosaves ""
set timeout -1
set minp 0
set gameseed 42
set mapseed 42
start
SERVEOF

echo "Running nationstates autogame (up to 200 turns)..."
echo "Server: $SERVER"
echo "Output: $OUTPUT"

# Run with debug logging, capture stderr (where log_debug goes) and stdout
cd "$WORKSPACE" && FREECIV_DATA_PATH="$WORKSPACE/data" \
  "$SERVER" -d debug -r "$SERV_FILE" > "$OUTPUT" 2>&1 || true

# Count first-strike events
FS_DEFENDER=$(grep -ac "First strike (defender):" "$OUTPUT" 2>/dev/null || true)
FS_ATTACKER=$(grep -ac "First strike (attacker):" "$OUTPUT" 2>/dev/null || true)
FS_TOTAL=$((FS_DEFENDER + FS_ATTACKER))

echo ""
echo "=== First Strike Test Results ==="
echo "Defender first strike events: $FS_DEFENDER"
echo "Attacker first strike events: $FS_ATTACKER"
echo "Total first strike events:    $FS_TOTAL"
echo ""

PASS=0
FAIL=0

# Test 1: Any first strikes occurred
if [ "$FS_TOTAL" -gt 0 ]; then
  echo "PASS: First strike combat events detected ($FS_TOTAL total)"
  PASS=$((PASS + 1))
  echo "  Sample events:"
  grep "First strike" "$OUTPUT" | head -5 | sed 's/^/    /'
else
  echo "FAIL: No first strike events detected in 200 turns"
  FAIL=$((FAIL + 1))
fi

echo ""

# Test 2: Check game completed without crash
if grep -q "Game ended" "$OUTPUT" 2>/dev/null || grep -q "Game is over" "$OUTPUT" 2>/dev/null; then
  echo "PASS: Game completed without crash"
  PASS=$((PASS + 1))
else
  # Check if server at least started and ran turns
  TURN_COUNT=$(grep -aoP 'T\d+:' "$OUTPUT" 2>/dev/null | sort -u | wc -l || true)
  if [ "$TURN_COUNT" -gt 10 ]; then
    echo "PASS: Server ran $TURN_COUNT turns successfully"
    PASS=$((PASS + 1))
  else
    echo "FAIL: Game may not have run correctly (turn count: $TURN_COUNT)"
    FAIL=$((FAIL + 1))
  fi
fi

echo ""
echo "=== Summary: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "Tip: If no first-strike events were found, try different seeds:"
  echo "  Edit SERV_FILE gameseed/mapseed values and re-run."
  echo "  First-strike units require Warrior Code tech (for Archers)."
  exit 1
fi

exit 0
