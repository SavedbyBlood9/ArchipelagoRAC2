# ArchipelagoRAC2 credits

ArchipelagoRAC2 is an independent OpenRAC adaptation of **[APRac2 by evilwb / Will Becker](https://github.com/evilwb/APRac2)**. APRac2 provided the original Going Commando Archipelago implementation, item and location definitions, world generation, access logic, YAML settings and gameplay behavior used as the basis for this port. Original copyright: Copyright (c) 2024 Will Becker. Its MIT license is retained in `third_party/APRac2-LICENSE.md` and the APWorld's upstream license notice.

**[OpenRAC](https://github.com/OpenRAC/OpenRAC)** provided the native game host and mod SDK. The native host overrides derive from **[OpenRAC/rac2-decomp](https://github.com/OpenRAC/rac2-decomp)** and retain their GPL-3.0-only notices and license under `host-patch/`. OpenRAC's SDK is an external MIT dependency.

Additional project dependencies and references:

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago): multiworld framework and network protocol; external framework dependency.
- [nlohmann/json](https://github.com/nlohmann/json): bundled MIT JSON library; notice retained in `third_party/nlohmann-json-LICENSE.MIT`.
- [OpenRAC mod examples](https://github.com/OpenRAC/openrac-mods): consulted for architecture; no implementation code copied.

Credit for original APRac2 functionality belongs to its upstream contributors. ArchipelagoRAC2 adds the OpenRAC adaptation and is not an official release of those upstream projects. Pinned source revisions are recorded in `sources.lock.json`. Original upstream copyright and license notices are preserved.
