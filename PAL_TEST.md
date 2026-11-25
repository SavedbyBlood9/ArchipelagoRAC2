> Historical validation of the 0.3/0.4 private-host implementation. For the API 1.40 preview, see README.md and GAMEPLAY_QUERIES.md. Old setup commands below refer to the archived releases.

# PAL SCES_516.07 local validation

Disc: Ratchet & Clank 2 (Europe, Australia), SCES_516.07, MD5 `e184fc2a495a4654f748a8e8c587261c`. OpenRAC develop `cef20495798f314cad4659bb3e9a457dfcec865a`; rac2-decomp `4ea93ceaf43aec055e19211d36512e847860bac2`. Windows x86-64 graphical host, API 1.19, mod 0.4.0.

Both discs' boot and 27 level executables were extracted for address/function comparison. PAL rendering assets were extracted to a workspace data folder. The patcher installed 33 callback mappings and twenty PAL-specific native overrides. Upstream PAL parity validation reported zero problems. Generated game-function bodies and retail files remain local and are excluded from publication.

A workspace-only helper advanced the title and requested a new Ship Shack campaign through the SDK. The game ran for 2,400 frames with a synthetic authenticated seed. It used isolated cards, settings, logs and plugin configuration. Neither the installed launcher nor the original game files or existing saves were modified.

Observed:

- All 33 gameplay hooks loaded, with native reward/save tracking active.
- Loopback authentication succeeded and 15 game-to-client reports arrived.
- Twelve rewards applied once: Lancer, Gravity Bomb, three planet coordinates, Dynamo, two Bolt Packs, Platinum Bolt, Nanotech Boost, Hypnomatic Part and progressive wrench.
- Final report: level 24, receipt cursor 12, bolts 20,000, platinum 1, boosts 1 and native option mask 7.
- Host exited with code 0.

The Yeedil placement tables have identical 741 moby index/class/spawn-ID tuples between these discs, including the final boss UID 197 (class 4576). Actual final victory still needs a campaign test.

Five native tests exercise both USA/PAL runtime memory, journal handling and TCP transport. Ten Python tests include real local WebSocket transport; three official Archipelago framework tests cover generation, options and cross-slot placement. All 18 pass.

These results verify PAL loading, campaign binding, receipt effects and bridge communication. They do not verify a complete PAL campaign, a real server multiworld completion, memory-card round trips or every localized menu/softlock scenario. Keep the release experimental and use separate PAL cards. No custom host executable, ISO, extracted assets or translated retail game code is distributed.

For local play:

```powershell
python tools/play_local.py --region pal --server wss://archipelago.gg:PORT --slot YourSlotName
```

In another checkout, also supply `--host PATH_TO_PATCHED_PAL_EXE --data-root PATH_TO_EXTRACTED_PAL_DATA`. Build instructions are in host-patch/README.md. Original YAML options and Archipelago identifiers are shared across the supported USA and PAL discs.
