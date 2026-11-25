# Required OpenRAC API integration

The API-preview client requires OpenRAC mod API 1.40 plus the generic RAC2 inventory/story hooks proposed in [OpenRAC PR #827](https://github.com/OpenRAC/OpenRAC/pull/827). It does not use the old APRac2-specific SDK hook aliases. The mod supports USA v1.01 and PAL; API-side query points also cover USA v2.00, which does not by itself add v2.00 memory support to this mod.

The proposed `on_play_query` API registers a callback during mod load, with exclusive ownership of the requested query kinds until unload. The host supplies the disc-correct original/alternate values. Unowned queries preserve retail behavior. No activation state is stored in game memory or saves; the client enables its decisions only while bound to the correct seed.

The OpenRAC integration adds neutral decision points to native build copies of twenty source functions. Its source-location/hash catalogue and generator live in OpenRAC, not this mod. Audited definition hashes and insertion counts must match on all three discs. The matching decompilation is untouched, and generated game-function bodies remain local build output.

This integration must be accepted and released by OpenRAC before ordinary stock releases can run the preview client. A successful local build is not upstream acceptance. The combined proposal now includes the fifteen hook mappings and gameplay queries; the old hook-only head is insufficient.

API-preview testing uses a separate source checkout and build, without installing the old private override files or save-restore activation patch. Standard OpenRAC build/extraction requirements still apply to a locally built host and the player's own supported disc.
