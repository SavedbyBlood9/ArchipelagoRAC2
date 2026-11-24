# Custom native host patch

Baseline: OpenRAC/OpenRAC develop `cef20495798f314cad4659bb3e9a457dfcec865a`, rac2-decomp `4ea93ceaf43aec055e19211d36512e847860bac2`. Requires the user's supported USA v1.01 or PAL SCES_516.07 disc and upstream Windows build dependencies.

```powershell
python tools/apply_host_patch.py C:/path/to/OpenRAC
```

This idempotently adds native hook declarations/parity exceptions and copies the twenty gated overrides into `port/game/rac2-ntsc/hand/aprac2`. It also provides an optional `OPENRAC_ONLY_GAME` CMake filter, a headless frontend compile guard, a bounded cast-record parser fix (Python 3.11+) and clears APRac2 activation after save restoration. Matching decompilation sources remain untouched.

Use upstream `tools/build_port.py rac2-ntsc --disc PATH --preset headless` for a headless build, or the normal graphical preset for play. Set CMake `OPENRAC_ONLY_GAME=rac2-ntsc` when limiting configuration to this game. Follow upstream toolchain/dependency instructions. The local build used `aprac2-headless` first, then the `aprac2-play` graphical preset reusing the same build directory. The graphical executable is therefore at `work/OpenRAC/port/build/aprac2-headless/openrac-rac2-ntsc.exe` in this workspace. `tools/play_local.py` finds it automatically. It does not replace the installed host.

Install the 0.3 mod in the resulting custom host and enable `enable_gameplay`. Missing hooks cause activation to fail. Keep test cards, settings and logs separate from existing campaigns.

Overrides are derived from the GPL-3.0-only OpenRAC/rac2-decomp project; see LICENSE and source headers. Hook-table and build-file additions are provided as part of this host integration. The remainder of the mod has separate MIT licensing. No retail code generated from the disc is included; do not redistribute a locally built host without reviewing upstream distribution requirements.

Regenerate the native overrides from the pinned decompilation with `python tools/generate_host_overrides.py C:/path/to/OpenRAC`; symbol facts are in `data/native-host-symbols.json`. The generator asserts each targeted source rewrite before producing files.

Public distributions omit generated `overrides/*.c` game-function bodies. `apply_host_patch.py` automatically runs the generator when these local files are missing. Keep the pinned OpenRAC/rac2-decomp checkout available. No compiled custom host or extracted game assets are distributed.

## PAL SCES_516.07

Use the pinned checkout above, initialize its decompilation submodule, and follow upstream PAL disc extraction/build requirements. Apply both the shared integration and PAL-specific callbacks/overrides with:

```powershell
python tools/apply_pal_host_patch.py C:/path/to/OpenRAC
```

Build `rac2-pal` using upstream `tools/build_port.py rac2-pal --disc PATH_TO_PAL_ISO --preset YOUR_GRAPHICAL_PRESET`. Set `OPENRAC_ONLY_GAME=rac2-pal` when selecting a single game. The mod requires this patched PAL host; a stock PAL executable lacks the custom callbacks. The PAL overrides retain their source's 50 Hz behavior and localized menu IDs. Generated bodies under `overrides-pal/*.c` stay local, just like the USA bodies.

`data/pal-host-symbols.json` records the mapped callbacks and source provenance. `src/pal_boot_moves.hpp` is generated from OpenRAC's PAL data movement facts with `tools/generate_pal_profile.py`. The source generator asserts every override rewrite, and the upstream parity checker should report no problems after applying the patch.

The local graphical PAL host is `work/OpenRAC/port/build/archipelagorac2-pal/openrac-rac2-pal.exe`. The helper selects it with `--region pal`; elsewhere pass `--host` and `--data-root`. Keep PAL memory cards separate from USA cards.
