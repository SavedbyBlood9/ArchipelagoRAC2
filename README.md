# ArchipelagoRAC2 0.3.1 (experimental)

Native Archipelago implementation for Going Commando USA v1.01 (`rac2/ntsc`). Preserves APRac2's game identity, 120 item IDs, 123 possible location IDs, original access logic and YAML settings.

The native adapter now implements item delivery, independent collection checks, NPC pickup views, coordinates, vendor item/ammo modes and base prices, currencies, progressive equipment, save-local receipt history, goal reporting, DeathLink, hub travel and gameplay settings. **This is an experimental implementation, not a validated full-campaign release.** See VALIDATION.md and PORTING.md for the remaining verification boundary.

Gameplay requires a custom OpenRAC host with `host-patch/` applied. The installed API 1.19 host alone does not expose all required hooks. The mod defaults to connection validation; enabling `enable_gameplay` on an unpatched host fails with a missing-hook message.

Based on **[evilwb/APRac2 by Will Becker](https://github.com/evilwb/APRac2)** and built for **[OpenRAC](https://github.com/OpenRAC/OpenRAC)**. APRac2 supplied the original randomizer logic and settings. See [CREDITS.md](CREDITS.md) for upstream attribution and licenses.

The existing internal mod ID, hook aliases and Archipelago game identity are retained for save and network compatibility. The displayed project/mod name and distributable filenames are ArchipelagoRAC2.

## Files

- `dist/ArchipelagoRAC2.apworld`: original world generation with native slot data instead of ISO patching.
- `templates/ArchipelagoRAC2.yaml`: original options and defaults.
- `dist/ArchipelagoRAC2-0.3.1-windows-x86_64.zip`: native mod.
- `client/client.py`: Archipelago WebSocket client and authenticated loopback bridge.
- `host-patch/`: additional hooks and native-only option overrides; source patcher in `tools/apply_host_patch.py`.

## Setup

1. Use Archipelago 0.6.9+ and install the supplied APWorld in `custom_worlds`. Remove the original APRac2 APWorld first: both register the same game. Generate a new seed using the YAML template; original PS2 seeds lack native slot data and are rejected.
2. Build the patched OpenRAC host following `host-patch/README.md`. Use a separate test data directory and memory cards.
3. Install the native mod into that custom host, set its bridge token/port, and enable experimental gameplay. Connect the sidecar before starting a **new** campaign. Existing unbound saves and saves from another seed/team/slot are rejected.

```powershell
python -m pip install -r client/requirements.txt
python client/client.py --server wss://archipelago.gg:PORT --slot YourSlotName
```

Use `ws://127.0.0.1:PORT` for a local room. Add `--password ROOM_PASSWORD` if required. Paste the printed token into the mod's Local client token setting; default local port is 38282. Gameplay settings come from generated YAML, not launcher overrides. Server passwords are not included in bridge snapshots or seed files.

The campaign starts at Ship Shack. Return with L1+R1+L2+R2+Select or the special menu shortcut. Randomized vendors use Up for items and Down for ammo. Local checks remain in save metadata during disconnection and resend on reconnection. Save rollback also rolls back receipt history so consumable rewards can replay consistently.

## Play with the locally built graphical host

Download the files from the [experimental v0.3.1 release](https://github.com/SavedbyBlood9/ArchipelagoRAC2/releases/tag/v0.3.1) into `dist/`, or use the source bundle that includes them. Build the patched graphical host locally from your supported disc. In the original development workspace the helper also detects the existing local host. From this folder:

```powershell
python -m pip install -r client/requirements.txt
python tools/play_local.py --server wss://archipelago.gg:PORT --slot YourSlotName
```

Add `--password` if needed. The helper waits for slot synchronization, configures the native mod automatically, then opens the game. Start a new campaign. Cards/settings/plugins/logs stay under `local-play/`; extracted disc and rendering assets are shared read-only from the supplied OpenRAC data folder. It leaves the installed launcher and its plugin configuration alone. In a different checkout, pass `--host PATH_TO_CUSTOM_EXE --data-root PATH_TO_EXTRACTED_DATA`. The helper expects a graphical host and requires the sidecar dependencies above.

## Build and test the mod

From a Visual Studio x64 tools prompt, with CMake, Ninja, Python and OpenRAC SDK 1.19+:

```powershell
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DOPENRAC_SDK=C:/path/to/OpenRAC/sdk
cmake --build build
ctest --test-dir build --output-on-failure
python -m unittest discover -s tests -v
python tools/test_world.py --archipelago C:/path/to/Archipelago --deps C:/path/to/dependencies
python tools/package_apworld.py
python tools/package_native_mod.py --sdk C:/path/to/OpenRAC/sdk --input build/package/aprac2_client --output dist
```

## Licenses

Mod, sidecar and APRac2-derived world code: MIT; notices in `third_party/`. Bundled nlohmann/json 3.12.0: MIT. OpenRAC SDK: external MIT dependency. **Native host overrides derive from OpenRAC/rac2-decomp and are GPL-3.0-only**, with their own license and attribution under `host-patch/`. Generated native game-function bodies are kept local and excluded from the repository and release source bundle. The patch tool regenerates them from your local OpenRAC decompilation checkout as needed. No retail disc assets or translated retail game code are distributed. Build the host locally from your own supported disc.

Version 0.3.1 is a license-packaging correction: native archives now include Will Becker's original APRac2 MIT notice verbatim as `LICENSE.APRac2`. The packager checks its bytes against the retained upstream license before completing. Gameplay and save/network identifiers are unchanged.
