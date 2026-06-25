# About
Freeciv21 is a open source strategy game. The goal is to design and make changes to allow for a games master hosting a Nation States region.

# Nation States
Nation States is a online browser game. The region in question is set in 1946 era of technology, with a custom map. 

# Modifications
The preference is first, mod the game, second script changes, third modify the engine. Keep code changes minimal as smaller PRs are more likely to be accepted.

# Layout
- nationstates directory with anything related to the Nation States Region and design for the mod.

# Coding Standards
Follow the [Freeciv21 coding guidelines](https://longturn.readthedocs.io/en/latest/Coding/guidelines.html) (also at `docs/Coding/guidelines.rst`). Key points:
- C++17 target
- All code must be formatted with `clang-format` using the repo's `.clang-format` config
- Naming: `all_lowercase_letters` for variables/functions, `UPPERCASE` for constants/enums, `m_` prefix for private members
- Doxygen `/** */` comments on all public functions/classes
- Use `const`, declare variables near first use, prefer references over pointers for new code
- Includes ordered most-specific to least-specific: self, generated, utility, common, dependency, ai, server, client, Qt, std
- Prefer using references over pointers for variables and function parameters.
- New code or modified code should adhere to modern c++ standards. 

# Building
```sh
cmake --build builds/linux-x64-gcc-release --parallel $(nproc)
```

# Testing
Three test suites exist. Run all with:
```sh
cd builds/linux-x64-gcc-release && ctest --output-on-failure
```
- `test_rulesets` - loads and validates all rulesets
- `test_server_cli` - server CLI tests
- `test_utility_paths` - utility path tests

# AI Autogame Testing
Run a fully automated AI-only game to verify engine changes don't cause crashes or regressions.
See `docs/Coding/hacking.rst` for full details.

A pre-made config exists at `data/test-autogame.serv`. The `timeout -1` autogame mode requires a Debug build:
```sh
# One-time: configure and build Debug
cmake -B builds/linux-x64-gcc-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug /workspace
cmake --build builds/linux-x64-gcc-debug --parallel $(nproc)

# Run an AI-only game (uses classic ruleset by default)
builds/linux-x64-gcc-debug/freeciv21-server -r data/test-autogame.serv
```

Custom test configs can override settings. Key options:
- `set timeout -1` — auto-advance turns (Debug builds only)
- `set minp 0` — no human players needed
- `set aifill N` — number of AI players
- `set endt N` — end at turn N
- `set gameseed 42` / `set mapseed 42` — reproducible results

To test with debug logging (e.g. verifying combat changes):
```sh
builds/linux-x64-gcc-debug/freeciv21-server -d debug -r data/test-autogame.serv 2>&1 | grep "your search term"
```

To stress-test overnight:
```sh
while( time builds/linux-x64-gcc-debug/freeciv21-server -r data/test-autogame.serv ); do date; done
```

Note: The default ruleset is `classic` (from `data/classic/`). To test ruleset changes in `civ2civ3`, add `set rulesetdir civ2civ3` to your .serv file.

# Formatting
Run clang-format on modified files before committing:
```sh
clang-format -i path/to/file.cpp path/to/file.h
```
