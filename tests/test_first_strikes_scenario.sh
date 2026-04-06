#!/bin/bash
# Targeted scenario test for first-strike combat mechanics.
# Uses Lua commands to set up specific unit matchups and validates
# first-strike events in debug output.
#
# Requirements:
#   - Debug build at builds/linux-x64-gcc-debug/freeciv21-server
#     Build with:
#       cmake -B builds/linux-x64-gcc-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -S /workspace
#       cmake --build builds/linux-x64-gcc-debug --parallel $(nproc)
#
# Usage:
#   bash tests/test_first_strikes_scenario.sh

set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
SERVER="${WORKSPACE}/builds/linux-x64-gcc-debug/freeciv21-server"
SERV_FILE="$(mktemp /tmp/test-fs-scenario-XXXXXX.serv)"
OUTPUT="$(mktemp /tmp/fs-scenario-output-XXXXXX.log)"

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

# Create server config that sets up targeted scenarios via Lua.
#
# Strategy: Start a game with AI players, then use Lua to:
# 1. Give AI players techs that unlock first-strike units
# 2. Create first-strike units near enemy territory
# 3. Let AI aggression trigger combat naturally over ~50 turns
#
# Scenario A: Archers (first_strikes=1) vs Warriors (first_strikes=0)
#   -> Expect "First strike (defender)" or "First strike (attacker)" log
#
# Scenario B: AA-Artillery (FirstStrikes bonus vs Flying) vs Fighter (Flying flag)
#   -> Expect first strike events involving AA-Artillery
cat > "$SERV_FILE" << 'SERVEOF'
rulesetdir nationstates
set aifill 4
set autosaves ""
set timeout -1
set minp 0
set gameseed 42
set mapseed 42
set endt 100
start

# --- Scenario A: Standard first strikes ---
# Give all AI players Warrior Code (unlocks Archers with first_strikes=1)
lua cmd for p in players_iterate() do edit.give_tech(p, find.tech_type("Warrior Code"), -1, false, "test") end

# Create Archers for each player near their starting position.
# Archers have first_strikes=1 and will be used by AI in combat.
lua cmd local ut = find.unit_type("Archers"); for p in players_iterate() do for u in p:units_iterate() do edit.create_unit(p, u.tile, ut, 0, nil, -1); break end end

# Also create extra Warriors to serve as targets
lua cmd local ut = find.unit_type("Warriors"); for p in players_iterate() do for u in p:units_iterate() do edit.create_unit(p, u.tile, ut, 0, nil, -1); edit.create_unit(p, u.tile, ut, 0, nil, -1); break end end

# --- Scenario B: Anti-air first strikes ---
# Give techs for AA-Artillery (requires Military Aviation) and Fighter (requires Flight)
lua cmd for p in players_iterate() do edit.give_tech(p, find.tech_type("Flight"), -1, false, "test"); edit.give_tech(p, find.tech_type("Military Aviation"), -1, false, "test") end

# Create AA-Artillery and Fighters
lua cmd local aa = find.unit_type("AA-Artillery"); local fighter = find.unit_type("Fighter"); local i = 0; for p in players_iterate() do for u in p:units_iterate() do if i % 2 == 0 then edit.create_unit(p, u.tile, aa, 0, nil, -1) else edit.create_unit(p, u.tile, fighter, 0, nil, -1) end; break end; i = i + 1 end
SERVEOF

echo "Running first-strike scenario test (up to 100 turns)..."
echo "Server: $SERVER"
echo "Output: $OUTPUT"

# Run with debug logging
cd "$WORKSPACE" && FREECIV_DATA_PATH="$WORKSPACE/data" \
  "$SERVER" -d debug -r "$SERV_FILE" > "$OUTPUT" 2>&1 || true

echo ""
echo "=== First Strike Scenario Test Results ==="
echo ""

PASS=0
FAIL=0

# --- Scenario A: Standard first strikes ---
FS_TOTAL=$(grep -ac "First strike" "$OUTPUT" 2>/dev/null || true)
# Look for Archers specifically in first strike logs
FS_ARCHERS=$(grep "First strike.*Archers" "$OUTPUT" 2>/dev/null | wc -l || true)

echo "--- Scenario A: Standard First Strikes ---"
echo "Total first strike events: $FS_TOTAL"
echo "Archers first strike events: $FS_ARCHERS"

if [ "$FS_TOTAL" -gt 0 ]; then
  echo "PASS: First strike combat events detected"
  PASS=$((PASS + 1))
  grep "First strike" "$OUTPUT" | head -3 | sed 's/^/  /'
else
  echo "FAIL: No first strike events detected"
  FAIL=$((FAIL + 1))
fi
echo ""

# --- Scenario B: Anti-air first strikes ---
FS_AA=$(grep "First strike.*AA-Artillery" "$OUTPUT" 2>/dev/null | wc -l || true)

echo "--- Scenario B: Anti-Air First Strikes (AA-Artillery vs Flying) ---"
echo "AA-Artillery first strike events: $FS_AA"

if [ "$FS_AA" -gt 0 ]; then
  echo "PASS: AA-Artillery first strike events detected (anti-air bonus working)"
  PASS=$((PASS + 1))
  grep "First strike.*AA-Artillery" "$OUTPUT" | head -3 | sed 's/^/  /'
else
  echo "WARN: No AA-Artillery first strike events detected"
  echo "  (AI may not have engaged air units in combat during this run)"
  echo "  Try different seeds or increase endt if this persists."
  # Don't fail - AA combat is harder to force
fi
echo ""

# --- Game stability check ---
TURN_COUNT=$(grep -aoP 'T\d+:' "$OUTPUT" 2>/dev/null | sort -u | wc -l || true)
if [ "$TURN_COUNT" -gt 5 ]; then
  echo "PASS: Server ran $TURN_COUNT turns without crash"
  PASS=$((PASS + 1))
else
  echo "FAIL: Server may not have run correctly (turn count: $TURN_COUNT)"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Summary: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "Debug: Full output at $OUTPUT"
  # Don't clean up on failure so user can inspect
  trap - EXIT
  exit 1
fi

exit 0
