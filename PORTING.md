# Native implementation and remaining verification

The 0.3.0 runtime replaces mapped item and coordinate grants with checks. NPC update hooks temporarily present collected-location state independently of received ownership, including early Clank receipts, wrench upgrades, trade rewards and Hypnomatic parts. Nested saves capture direct-write checks before serializing real inventory. Platinum/boost/part rewards derive from received items; their physical pickups remain checks.

The journal binds seed/team/slot and records receipt cursor, applied IDs, checks, visited planets, incoming deaths and victory using SDK save_data_get/set. Native reward callbacks execute on the game thread. Ordinary NPC saves restore actual inventory before serialization and resume temporary NPC views afterward. This protects the tested save paths; actual disk-save fault injection remains unverified.

The source patch adds hooks for otherwise inaccessible gameplay callbacks and twenty native overrides for challenge selection, revisit rewards, extras and hub shortcut. Control bytes activate these only while the mod is running and are cleared after a save restore. The matching decompilation sources are not changed; overrides apply to native build copies.

Remaining release validation:

- Complete actual two-player and cross-game campaigns with all options, including early item receipts, Endako, prison, travel, vendors and final victory.
- Verify goal UID/state detection, native save reloads, actual reward tables and each source-derived menu override in the running game.
- Verify the seven native controller/gate overrides for early-item respawns and audit remaining ammo-crate and presentation behavior. Native hooks and overrides are not proof of every original patch's behavior.
- Add richer received-item/player names and vendor labels; current reward notices identify local item names and remote vendor previews use a generic model.
- Complete extended graphical gameplay validation. A graphical host is now built and passed an OpenGL smoke test with existing extracted rendering assets; see LOCAL_TEST.md.

USA v1.01 and PAL SCES_516.07 have separate native address profiles and host overrides. PAL boot addresses are translated before SDK overlay relocation. Other revisions, including Greatest Hits, remain unsupported. Runtime tests do not establish full campaign parity.
