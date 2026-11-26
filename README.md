# ArchipelagoRAC2 0.6.1 (API preview)

Archipelago multiworld for Going Commando USA v1.01 and v2.00 and Locked & Loaded PAL SCES_516.07 on OpenRAC. Original APRac2 game identity, item/location IDs, YAML options and access logic are retained.

This version moves the twenty private gameplay overrides into mod-owned decisions using the proposed OpenRAC gameplay-query API 1.40. It uses generic SDK hook names and no activation bytes, private packaging aliases, generated game-function bodies or host-patch installer.

**API 1.40 and the hooks this build needs are in OpenRAC's dev launcher (`v1.1.1-dev.1291` and later) but not yet in a stable release.** Until OpenRAC publishes them, use the dev launcher or a host built from `develop`. Once released, the same mod runs on a stock OpenRAC without a separate APRac2 host patch. The released v0.4.0 remains a separate legacy custom-host build.

The mod's id is `archipelago-rac2` from 0.5.0 on (0.4.0 and earlier were `aprac2-openrac-dev`). The launcher treats it as a new mod: remove the old one, and set the token and port again.

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

Use `--region ntsc` for USA v1.01 and `--region ntsc2` for USA v2.00 (both are `SCUS_972.68`; with `auto`, an extracted `port/ntsc2` and no `port/ntsc` means v2.00). The development workspace also has default host/data paths. API-preview cards, settings and logs stay under `local-play/api40/`; installed launcher files and existing cards are not replaced. No custom host executable or game assets are distributed.

## Build and package

The client builds on Windows, Linux, macOS and Android (Winsock on Windows, POSIX sockets elsewhere: `src/net.hpp`). With CMake, Ninja, Python and a C++17 compiler (on Windows, a Visual Studio tools prompt):

```powershell
python tools/fetch_sdk.py   # the SDK sdk.lock pins, into .sdk/ (once OpenRAC releases SDK 1.40)
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
# or, until then, against a checkout of OpenRAC's develop branch:
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DOPENRAC_SDK=C:/path/to/OpenRAC/sdk
cmake --build build
ctest --test-dir build --output-on-failure
python -m unittest discover -s tests -v
python tools/test_world.py --archipelago C:/path/to/Archipelago --deps C:/path/to/dependencies
python tools/package_apworld.py
python tools/package_native_mod.py --sdk C:/path/to/OpenRAC/sdk --input build/package/aprac2_client --output dist
```

The archive is `archipelago-rac2-<version>-<platform>.zip`, the name the launcher and the OpenRAC mod index look for. `-DAPRAC2_PROBE=ON` also builds the development probe (`aprac2-openrac-probe`), which releases leave out.

A tag `v<version>` makes the workflow (`.github/workflows/build.yml`) build and test the client on Windows, Linux and macOS, build it for Android, and publish every platform's archive, the APWorld, the YAML template and `SHA256SUMS` as a pre-release. Every push and pull request is built and tested too. Until OpenRAC releases Mod SDK 1.40, the workflow builds against OpenRAC's own `sdk/` at the commit its dev launcher was built from (`OPENRAC_REF` in the workflow), so releases match that dev build.

Packaging uses the SDK's standard bindings and byte-verifies the original APRac2 MIT notice as LICENSE.APRac2. Mod/sidecar/world code is MIT; nlohmann/json is MIT. The proposed OpenRAC query integration is maintained separately under OpenRAC's licenses. No retail code or assets are bundled.

## Discs

The mod's facts are USA v1.01 addresses. On PAL and USA v2.00 it translates each one through that disc's boot-program moves, generated from OpenRAC's `port/game/rac2-<disc>/release/data_moves.tsv` by `tools/generate_disc_profiles.py <OpenRAC checkout>` into `src/pal_boot_moves.hpp` and `src/ntsc2_boot_moves.hpp` (checked in, from OpenRAC `b005a7b`). Every address the mod reads or writes is in a mapped range on both. All 32 hook points and the 20 gameplay query points exist on all three discs. A seed lists the discs it was made for (`supported_discs`); seeds from before v2.00 list only `ntsc` and `pal`, which the mod does not enforce, so they play on v2.00 too.

Full campaign and real multiworld completion remain experimental. Current and historical validation are distinguished in VALIDATION.md.
