# Original YAML settings

USA v1.01 and PAL SCES_516.07 share the same YAML template. All 15 scalar game options retain upstream defaults, ranges and generation rules. All are transported in native slot data. Native behavior below requires experimental gameplay on an API 1.40 host; implementation does not establish full playthrough parity.

| YAML setting | Implementation |
|---|---|
| death_link | Native death edge reporting, incoming deaths and saved incoming-event deduplication |
| starting_weapons | Original four selection modes; native delivery through indexed starting-item history |
| randomize_megacorp_vendor | Original pool plus visited-planet item checks, separate ammo mode and base weapon prices |
| randomize_gadgetron_vendor | Original pool plus independent purchases and ammo mode |
| exclude_very_expensive_items | Original RYNO II/Zodiac placement rules |
| skip_wupash_nebula | Native completion flag before travel |
| enable_bolt_multiplier | Native kill reward callback temporarily enables the multiplier outside NG+ |
| no_revisit_reward_change | Mod-owned query level-data override retains base bolt and XP rewards |
| no_kill_reward_degradation | Native repeated-kill scale table set to 100% |
| free_challenge_selection | Mod-owned query arena, hoverbike and spaceship menu/input overrides |
| nanotech_xp_multiplier | Original inverse scaling of health XP requirements (20..600%, default 100) |
| weapon_xp_multiplier | Original inverse scaling of weapon XP requirements (30..600%, default 100) |
| extra_spaceship_challenge_locations | Original nine optional checks and native mission-flag scanning |
| extend_weapon_progression | Extended upgrade thresholds and native level-up calls; Walloper and Decoy XP handling |
| first_person_mode_glitch_in_logic | Original disabled/easy/medium/hard access rules; native extras menu available outside NG+ |

Archipelago common options, including start_inventory_from_pool, accessibility, item links, excluded locations and starting hints, retain framework processing. Starting items are included in the native receipt stream. Launcher settings control only the bridge and experimental activation.
