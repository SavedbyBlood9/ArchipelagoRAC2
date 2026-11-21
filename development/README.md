# ArchipelagoRAC2 native client 0.3.0 (experimental)

Going Commando USA v1.01, OpenRAC mod API 1.19. Implements the native Archipelago adapter, item delivery, independent location checks, vendors, save metadata, DeathLink, hub travel and original YAML gameplay settings.

Gameplay requires the custom OpenRAC host built with host-patch from the source package. The installed stock host lacks required hooks. The Experimental native gameplay setting defaults off; leave it off for connection validation on an ordinary host. A full campaign and real multiworld completion remain unverified.

Use tools/play_local.py from the source package to connect the sidecar and configure the local graphical host automatically. For manual setup, run client/client.py, paste the printed token into Local client token, match the bridge port and enable gameplay on the custom host. Connect before starting a new campaign. Existing unbound saves and saves from another seed/team/slot are rejected. Keep separate test cards.

See the source package README.md, SETTINGS.md, LOCAL_TEST.md and PORTING.md for implementation and validation scope. The DLL includes nlohmann/json (MIT); its notice is included. Host overrides have separate GPL licensing and are supplied only in the source package.

Based on [evilwb/APRac2 by Will Becker](https://github.com/evilwb/APRac2), using the [OpenRAC host and SDK](https://github.com/OpenRAC/OpenRAC). Full attribution is included in README-CREDITS.md (CREDITS.md in the source package).
