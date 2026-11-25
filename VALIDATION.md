# API-preview validation (0.5.0)

Passed on Windows x86-64 using the proposed public API 1.40 and the standard SDK binding catalogue:

- Seven native CTest cases, including USA/PAL active-query behavior, independent physical/received Box Breaker flags, disabled YAML options, journal and transport tests. Private activation bytes remain untouched.
- Ten Python bridge/contract tests and three official Archipelago world/fill/two-slot tests.
- Query registry tests cover default passthrough, ownership conflicts, unload, callback exceptions, reentrancy and invalid outputs. Four source-generation tests validate all twenty query-point functions on all three discs and reject audited source drift.
- 99 SDK tool tests pass with native Windows ABI generation. Existing upstream ABI rows remain unchanged; Linux-target ABI verification remains for CI.
- RAC2 parity reports zero problems; parity suites pass (12 + 2). Launcher core: 608 passed, one existing ignored.
- USA and PAL API hosts compiled and each completed an isolated 2,400-frame synthetic campaign with bridge authentication, twelve receipts, 20,000 bolts, one platinum bolt, one nanotech boost and clean exit. These runs used neutral query integration, not the legacy private-host patch. The final merged USA/PAL hosts also completed those runs: USA emitted 13 bridge reports, PAL 14; both exited 0 with all twelve receipts applied. The final API commit adds documentation/notices and a formatting-only declaration correction to the built integration.
- Native ZIP packaging uses public bindings and verifies the original APRac2 MIT notice byte for byte. No retail assets, generated game-function bodies or host executables are distributed.

Full campaigns, every challenge/menu query interaction, real multiworld completion and memory-card round trips remain unverified. USA v2.00 has source/query generation coverage, but no runtime test and no mod memory profile. Stock releases cannot run this preview until upstream accepts and releases the proposed API.

The historical results below describe the old private-host releases, not the new API-preview build.

---

# Validation: 0.3.0 experimental

Passed on Windows x86-64:

- Four CTest cases: pass-through SDK behavior; journal replay/rollback/binding; authenticated bidirectional native TCP transport; actual runtime adapter exercised by a mock host.
- Runtime assertions cover item effects and duplicate replay, independent physical/received currency, NPC nested saves, direct Clank pickups, prison restoration without false checks, wrench checks across nested saves, kill multiplier, reward scale table, randomized vendor checks/prices and wrong-seed rejection.
- Nine Python tests, including a real local WebSocket-to-TCP integration, validate contract IDs, options, synchronization, reconnect, checks, goal and DeathLink.
- Three official Archipelago framework tests cover YAML/slot data/output, restrictive fill across eight option combinations and two-player cross-slot placements. Generated worlds are logically beatable under upstream rules.
- Custom headless host built and ran 3,600 frames with all 33 hooks loaded. A scratch Ship Shack campaign applied seven rewards once and reported the expected 20,000 bolts and received currency counts through the authenticated bridge; clean exit. A second run delivered twelve rewards including starting weapons/coordinates. The final graphical host also completed a 2,400-frame windowed campaign with twelve receipts, fourteen bridge reports and the expected reward totals. See LOCAL_TEST.md.

The provided disc matches APRac2's supported USA v1.01 MD5. Installed launcher is 1.0.3, bundled host is 1.0.2 with mod API 1.19. No installed launcher, game executable, disc or existing save was modified.

Custom-host build and native smoke-test results are recorded separately in LOCAL_TEST.md. A full campaign, real multiworld playthrough, disk-save fault injection and all gameplay menu combinations remain unverified. Treat the mod as experimental.

## 0.3.1 license-packaging correction

No gameplay behavior changed. Native archive packaging now copies and verifies the exact bytes of the original APRac2 MIT notice as LICENSE.APRac2. The primary MIT notice also retains Will Becker's copyright. Prior campaign tests above describe the 0.3.0 gameplay implementation.

## 0.4.0 PAL integration

Five native CTest cases, ten Python tests (including the real local WebSocket bridge), and three official Archipelago framework tests pass: 18 total. The runtime adapter is exercised separately against USA and PAL mock-host memory, including grants, checks, vendor behavior, options and journal handling. Native seed contracts accept both supported discs and retain legacy USA target compatibility.

The supplied Europe/Australia disc is SCES_516.07, MD5 `e184fc2a495a4654f748a8e8c587261c`. PAL callback mappings, twenty source override rewrites and the upstream parity checker were validated against the pinned checkout. The final boss placement's UID/class matches the USA data; that comparison alone does not validate final victory behavior in a playthrough.

A full PAL campaign, real server multiworld completion, memory-card round trips and every localized menu combination remain unverified.

The actual PAL graphical host compiled and completed a 2,400-frame isolated campaign on level 24. All 33 hooks loaded; the native bridge authenticated and emitted 15 reports. Twelve rewards applied, with cursor 12, bolts 20,000, platinum 1, nanotech boosts 1 and native option mask 7. Exit code was 0. See PAL_TEST.md for the setup and limits.
