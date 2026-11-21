# Validation: 0.3.0 experimental

Passed on Windows x86-64:

- Four CTest cases: pass-through SDK behavior; journal replay/rollback/binding; authenticated bidirectional native TCP transport; actual runtime adapter exercised by a mock host.
- Runtime assertions cover item effects and duplicate replay, independent physical/received currency, NPC nested saves, direct Clank pickups, prison restoration without false checks, wrench checks across nested saves, kill multiplier, reward scale table, randomized vendor checks/prices and wrong-seed rejection.
- Nine Python tests, including a real local WebSocket-to-TCP integration, validate contract IDs, options, synchronization, reconnect, checks, goal and DeathLink.
- Three official Archipelago framework tests cover YAML/slot data/output, restrictive fill across eight option combinations and two-player cross-slot placements. Generated worlds are logically beatable under upstream rules.
- Custom headless host built and ran 3,600 frames with all 33 hooks loaded. A scratch Ship Shack campaign applied seven rewards once and reported the expected 20,000 bolts and received currency counts through the authenticated bridge; clean exit. A second run delivered twelve rewards including starting weapons/coordinates. The final graphical host also completed a 2,400-frame windowed campaign with twelve receipts, fourteen bridge reports and the expected reward totals. See LOCAL_TEST.md.

The provided disc matches APRac2's supported USA v1.01 MD5. Installed launcher is 1.0.3, bundled host is 1.0.2 with mod API 1.19. No installed launcher, game executable, disc or existing save was modified.

Custom-host build and native smoke-test results are recorded separately in LOCAL_TEST.md. A full campaign, real multiworld playthrough, disk-save fault injection and all gameplay menu combinations remain unverified. Treat the mod as experimental.
