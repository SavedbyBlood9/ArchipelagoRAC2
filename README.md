# ArchipelagoRAC2 0.5.0 (API preview)

Archipelago multiworld for Going Commando USA v1.01 and Locked & Loaded PAL SCES_516.07 on OpenRAC. Original APRac2 game identity, item/location IDs, YAML options and access logic are retained.

This version moves the twenty private gameplay overrides into mod-owned decisions using the proposed OpenRAC gameplay-query API 1.40. It uses generic SDK hook names and no activation bytes, private packaging aliases, generated game-function bodies or host-patch installer.

**API 1.40 is an integration proposal, not a claim that current stock OpenRAC releases support this build.** Until that API and the required hooks are merged and released upstream, use the matching API-preview host. Once released, the same mod will use the ordinary API without a separate APRac2 host patch. The released v0.4.0 remains a separate legacy custom-host build.

Based on [evilwb/APRac2 by Will Becker](https://github.com/evilwb/APRac2), using [OpenRAC](https://github.com/OpenRAC/OpenRAC). Original copyright and MIT notices are retained. See CREDITS.md and GAMEPLAY_QUERIES.md.

## Setup

1. Install the supplied APWorld with Archipelago 0.6.9+ in `custom_worlds`, replacing the original APRac2 APWorld (both register the same game). Generate a native seed with the YAML template.
2. Use an OpenRAC host with the generic inventory/story hooks and gameplay queries (API 1.40). The preview integration is documented in API_REQUIREMENTS.md. Do not run the old host patcher on it.
3. Install the native archive, configure the sidecar token/port and enable experimental gameplay. Connect before starting a new campaign. Keep separate cards; existing unbound or wrong-seed saves are rejected.

```powershell
python -m pip install -r client/requirements.txt
python client/client.py --server wss://archipelago.gg:PORT --slot YourSlotName
```

Add `--password` if needed. Paste the sidecar's printed token into the mod's local client token setting; default loopback port is 38282. Gameplay settings come from the generated YAML. Passwords are not included in bridge snapshots or seed files.

The campaign starts at Ship Shack. L1+R1+L2+R2+Select and the shortcut menu request return travel. Randomized vendors use Up for items and Down for ammo. Checks survive disconnection in save metadata and resend on reconnect; save rollback also rolls back consumable receipt history.

## Local preview helper

Use the matching API-preview graphical host and extracted assets:

```powershell
python tools/play_local.py --region pal --host PATH_TO_API40_EXE --data-root PATH_TO_PAL_DATA --server wss://archipelago.gg:PORT --slot YourSlotName
```

Use `--region ntsc` for USA v1.01. The development workspace also has default host/data paths. API-preview cards, settings and logs stay under `local-play/api40/`; installed launcher files and existing cards are not replaced. No custom host executable or game assets are distributed.

## Build and package

From a Visual Studio tools prompt, with CMake, Ninja, Python and the matching SDK 1.40 preview:

```powershell
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DOPENRAC_SDK=C:/path/to/OpenRAC/sdk
cmake --build build
ctest --test-dir build --output-on-failure
python -m unittest discover -s tests -v
python tools/test_world.py --archipelago C:/path/to/Archipelago --deps C:/path/to/dependencies
python tools/package_apworld.py
python tools/package_native_mod.py --sdk C:/path/to/OpenRAC/sdk --input build/package/aprac2_client --output dist
```

Packaging uses the SDK's standard bindings and byte-verifies the original APRac2 MIT notice as LICENSE.APRac2. Mod/sidecar/world code is MIT; nlohmann/json is MIT. The proposed OpenRAC query integration is maintained separately under OpenRAC's licenses. No retail code or assets are bundled.

Full campaign and real multiworld completion remain experimental. Current and historical validation are distinguished in VALIDATION.md.
