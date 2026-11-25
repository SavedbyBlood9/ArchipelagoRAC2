# Native integration and remaining work

The API-preview implementation uses ordinary SDK hooks for receipts, checks, saves, vendors and story rewards, plus synchronous gameplay-query callbacks for the twenty decisions documented in GAMEPLAY_QUERIES.md. It no longer ships private native game-function replacements or writes activation bytes. Stock-host availability depends on OpenRAC accepting and releasing the proposed API 1.40 integration.

The journal still binds seed/team/slot and tracks receipt cursor, checks, visits, deaths and victory through save_data_get/set. Existing nested-save handling restores real received inventory before serialization. All original item/location IDs and YAML settings remain unchanged.

Remaining validation includes full USA/PAL campaigns, real cross-game/two-player completion, memory-card round trips, every challenge-menu combination, early receipts and progression paths. All-disc API queries do not imply that the mod's memory profile supports USA v2.00. Historical 0.3/0.4 private-host tests remain documented separately and must not be presented as tests of the new API-preview build.
