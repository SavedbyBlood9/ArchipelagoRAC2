// SPDX-License-Identifier: MIT
// Connects the native game to Archipelago. Experimental gameplay requires the patched host.
#include "openrac/mod.hpp"
#include "bridge.hpp"
#include "disc.hpp"
#include "runtime.hpp"
#include <memory>

namespace {
rac2ap::Bridge bridge;
std::string last;
std::unique_ptr<rac2ap::Runtime> runtime;
void load(openrac::Mod& mod) {
    if (mod.game() != "rac2" || !rac2ap::supported_disc(std::string(mod.version())))
        throw openrac::Error("ArchipelagoRAC2 requires Going Commando USA v1.01 or v2.00, or Locked & Loaded SCES_516.07");
    auto token=mod.setting<std::string>("bridge_token");
    int port=mod.setting<int>("bridge_port");
    if (token.size()<16 || port<1 || port>65535)
        throw openrac::Error("Set bridge_token from the ArchipelagoRAC2 client console and a valid bridge_port first");
    if(mod.setting<bool>("enable_gameplay")) {
        runtime=std::make_unique<rac2ap::Runtime>(&mod.api(),mod.handle(),bridge);
        runtime->install();
    }
    bridge.start(port,token);
    last.clear();
    mod.on_frame([&mod] {
        if(runtime)return;
        auto state=bridge.snapshot();
        std::string line;
        if (state.is_null()) line="ArchipelagoRAC2: waiting for the local sidecar";
        else if (!state.value("error",std::string{}).empty()) line="ArchipelagoRAC2: "+state["error"].get<std::string>();
        else if (state.value("synced",false)) {
            line="ArchipelagoRAC2: native seed and YAML received. Enable experimental gameplay on an API 1.40 host to play.";
        } else line="ArchipelagoRAC2: waiting for the Archipelago slot and item synchronization";
        if (line!=last) { mod.info(line); last=line; }
    });
    mod.info(runtime?"ArchipelagoRAC2 experimental native gameplay loaded":"ArchipelagoRAC2 connection validation loaded; gameplay setting is off");
}
}
OPENRAC_MOD_CPP("archipelago-rac2", "0.6.0", load)
extern "C" OPENRAC_MOD_EXPORT void openrac_mod_unload(void) { bridge.stop(); runtime.reset(); }
