# Where the twenty override behaviors now live

All decisions below are implemented in `Runtime::play_query` in the native mod. The host's neutral query points supply original values; they contain no Archipelago options, seed state, item receipts or hub destination. API callbacks are removed automatically on unload. A disconnected bound campaign retains its synchronized settings; an unbound or rejected campaign leaves queries unchanged.

| Former override | Public decision kind | Mod behavior |
|---|---|---|
| Level moby data/rewards | REVISIT_BOLTS / REVISIT_XP | Choose first-visit rewards when no_revisit_reward_change is enabled |
| Extras unlock menu | MENU_TEXT / MENU_DATA | Use supplied unlocked values for the first two entries |
| Shortcut menu | MENU_ACTION | Cancel its original action and request Ship Shack through play_travel |
| Maktar challenge menu | CHALLENGE_AVAILABLE | Allow prerequisites when free_challenge_selection is enabled |
| Joba challenge menu | CHALLENGE_AVAILABLE | Same |
| Maktar previous panel | CHALLENGE_AVAILABLE | Same |
| Maktar next panel | CHALLENGE_AVAILABLE | Same |
| Joba previous panel | CHALLENGE_AVAILABLE | Same |
| Joba next panel | CHALLENGE_AVAILABLE | Same |
| Spaceship menu labels | CHALLENGE_AVAILABLE | Same |
| Spaceship selection input | CHALLENGE_AVAILABLE | Same |
| Hoverbike menu labels | CHALLENGE_AVAILABLE | Same |
| Hoverbike selection input | CHALLENGE_AVAILABLE | Same |
| Oozla controller | ITEM_RESPAWN | Prevent received equipment from triggering vanilla return placement |
| Maktar controller | ITEM_RESPAWN | Same |
| Barlow spawn controller | ITEM_RESPAWN | Same |
| Joba collectible controller | ITEM_RESPAWN | Same |
| Tabora controller | ITEM_RESPAWN | Same |
| Damosel trigger controller | ITEM_RESPAWN | Same; other trigger uses remain unchanged |
| Swamp-monster moving gate | HERO_OVERRIDE | Use the physical Box Breaker pickup flag for its guard |

Localized text and menu-data addresses come from the running disc's query alternate; the mod does not hardcode PAL/USA label IDs. Shared reward, menu and respawn fields are not temporarily faked, and private 0x1A7B51/52/53/58 control writes are removed. The existing native receipt journal, physical checks, vendor behavior and original fifteen YAML options remain in the mod.

Default queries and unload/failure cleanup are covered by host-registry tests. USA/PAL runtime tests cover active, unbound and rejected-seed decisions, reward alternates, menu data, travel and independent physical/received Box Breaker flags, and verify that no activation bytes are written. Source generation checks all twenty points on all three discs and fails closed on source drift. Full campaign and all menu interactions still need playthrough validation.
