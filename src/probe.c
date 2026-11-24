/* SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <string.h>
#include "openrac/openrac_mod.h"
#include "openrac/games/rac2.h"

static const openrac_api* host;
static openrac_mod* handle;
static openrac_rac2_Item_Give give_original;
static openrac_rac2_Item_Equip equip_original;
static openrac_rac2_Planet_Unlock unlock_original;
static openrac_rac2_Vendor_BuildList vendor_original;
static openrac_rac2_Level_Load load_original;

static void trace(const char* event, int value) {
    char line[128];
    snprintf(line, sizeof line, "ArchipelagoRAC2 probe: %s(%d)", event, value);
    host->log(handle, OPENRAC_LOG_INFO, line);
}

static void give(int32_t id) { trace("Item_Give", id); give_original(id); }
static int32_t equip(int32_t id) { trace("Item_Equip", id); return equip_original(id); }
static void unlock(int32_t id) { trace("Planet_Unlock", id); unlock_original(id); }
static void vendor(int32_t hide) { trace("Vendor_BuildList", hide); vendor_original(hide); }
static int32_t level_load(int32_t load, int32_t resume) {
    trace("Level_Load", load);
    return load_original(load, resume);
}

OPENRAC_MOD_EXPORT void openrac_mod_query(openrac_mod_info* out) {
    out->api_major = OPENRAC_MOD_API_MAJOR;
    out->api_minor = OPENRAC_MOD_TARGET_MINOR;
    out->id = "aprac2-openrac-probe";
    out->version = "0.2.0";
}

OPENRAC_MOD_EXPORT int openrac_mod_load(const openrac_api* api, openrac_mod* mod) {
    host = api;
    handle = mod;
    if (!api->game || strcmp(api->game, "rac2") || !api->version || (strcmp(api->version, "ntsc") && strcmp(api->version, "pal"))) {
        api->fail(mod, "ArchipelagoRAC2 probe requires Going Commando USA v1.01 or Locked & Loaded PAL (rac2/ntsc or rac2/pal)");
        return 1;
    }
    /* The host checks the manifest/API before loading; hook errors still get a precise reason. */
#define TAKE(point, replacement, original) do { \
    int result = OPENRAC_RAC2_HOOK(api, mod, point, replacement, original); \
    if (result != OPENRAC_HOOK_OK) { \
        api->fail(mod, "ArchipelagoRAC2 probe: unavailable or incompatible hook " #point); \
        return 1; \
    } \
} while (0)
    TAKE(Item_Give, give, &give_original);
    TAKE(Item_Equip, equip, &equip_original);
    TAKE(Planet_Unlock, unlock, &unlock_original);
    TAKE(Vendor_BuildList, vendor, &vendor_original);
    TAKE(Level_Load, level_load, &load_original);
#undef TAKE
    api->log(mod, OPENRAC_LOG_INFO,
             "ArchipelagoRAC2 compatibility probe loaded. Gameplay passes through unchanged. Archipelago is not implemented.");
    return 0;
}
