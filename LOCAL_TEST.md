# Local native gameplay validation

On 2026-11-19, built a custom Going Commando USA v1.01 headless host from the pinned OpenRAC source with the supplied native hooks and overrides.

Ran it for 3,600 frames with the 0.3.0 native gameplay mod enabled, an authenticated synthetic seed, and all gameplay toggles enabled. A workspace-only test helper advanced the title and started a new campaign at Ship Shack through the SDK. The test used separate cards, settings, logs, plugin configuration and crash folders; only extracted disc assets were shared read-only by directory junction. Installed game/launcher files and existing saves were untouched.

Observed:

- All 33 gameplay hooks loaded successfully.
- The native bridge authenticated and produced 23 game-to-client reports.
- Native campaign binding activated on level 24, load 1.
- Seven test rewards applied once: Dynamo, two Bolt Packs, Platinum Bolt, Nanotech Boost, Hypnomatic Part and progressive wrench.
- Final reports retained cursor 7, bolts 20,000, platinum 1, boosts 1 and native option mask 7 throughout continued execution.
- Host exited with code 0 after 3,600 frames.

This proves native loading, binding, effects and bidirectional transport in a running campaign, beyond the mock-host tests. It does not establish location reachability throughout the campaign, real server multiworld completion, actual memory-card reloads, every menu interaction or every original softlock patch.

A second native run (2,400 frames) included both starting weapons and three starting coordinates: all twelve rewards were applied once, with cursor 12 and bolts still 20,000. It exited cleanly.

The graphical custom host also compiled and linked, initialized OpenGL on the RTX 3070 Ti, loaded all gameplay hooks and rendered 422 level-0 models using the existing extracted assets. Its 30-frame windowed smoke test exited with code 0. The build wrapper assumed a preset-named output directory when writing its final metadata; the executable linked correctly, and metadata was written beside the actual executable. No installed host was replaced. The earlier 0.2 installed-host two-frame test covered connection validation only and is superseded for native effects by this run.

The final native regression suite also covers saves nested in wrench pickups and ensures prison inventory restoration cannot create Endako checks. Twenty native source overrides compile, including the seven controller/gate changes.

Final windowed campaign run after all changes: 2,400 frames, all 33 hooks loaded, twelve receipts applied, fourteen authenticated reports, final cursor 12 and bolts 20,000, exit 0. This used the rebuilt graphical host with all twenty native overrides and existing extracted rendering assets.
