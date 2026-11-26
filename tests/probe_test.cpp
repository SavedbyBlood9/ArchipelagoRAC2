#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
extern "C" {
#include "../src/probe.c"
}

static std::map<std::string, void*> replacements;
static std::string failed, missing;
static int calls, last;
static void require(bool ok) { if (!ok) { std::cerr << "probe assertion failed\n"; std::exit(1); } }
static void mock_void(int32_t v) { ++calls; last = v; }
static int32_t mock_int(int32_t v) { ++calls; last = v; return 123; }
static int32_t mock_load(int32_t a, int32_t b) { ++calls; last = a + b; return 456; }
static void mock_log(openrac_mod*, int, const char*) {}
static void mock_fail(openrac_mod*, const char* msg) { failed = msg; }
static int mock_hook(openrac_mod*, const char* name, const char* sig, void* replacement, void** original) {
    if (missing == name) return OPENRAC_HOOK_UNKNOWN;
    replacements[name] = replacement;
    std::string signature(sig);
    if (std::string(name) == "Level_Load") {
        require(signature == "i32(i32,i32)"); *original = reinterpret_cast<void*>(&mock_load);
    } else if (std::string(name) == "Item_Equip") {
        require(signature == "i32(i32)"); *original = reinterpret_cast<void*>(&mock_int);
    } else {
        require(signature == "void(i32)"); *original = reinterpret_cast<void*>(&mock_void);
    }
    return OPENRAC_HOOK_OK;
}

int main() {
    openrac_api api{};
    api.size = sizeof api; api.api_major = 1; api.api_minor = 20;
    api.game = "rac2"; api.version = "ntsc";
    api.log = mock_log; api.fail = mock_fail; api.hook = mock_hook;
    require(openrac_mod_load(&api, nullptr) == 0);
    require(replacements.size() == 5);
    reinterpret_cast<openrac_rac2_Item_Give>(replacements["Item_Give"])(36);
    require(calls == 1 && last == 36);
    require(reinterpret_cast<openrac_rac2_Item_Equip>(replacements["Item_Equip"])(13) == 123);
    require(calls == 2 && last == 13);
    reinterpret_cast<openrac_rac2_Planet_Unlock>(replacements["Planet_Unlock"])(2);
    require(calls == 3 && last == 2);
    reinterpret_cast<openrac_rac2_Vendor_BuildList>(replacements["Vendor_BuildList"])(1);
    require(calls == 4 && last == 1);
    require(reinterpret_cast<openrac_rac2_Level_Load>(replacements["Level_Load"])(3, 1) == 456);
    require(calls == 5 && last == 4);
    api.game = "rac1"; replacements.clear();
    require(openrac_mod_load(&api, nullptr) != 0 && replacements.empty());
    api.game = "rac2"; api.version = "pal";
    require(openrac_mod_load(&api, nullptr) == 0 && replacements.size() == 5);
    api.version = "ntsc2"; replacements.clear();
    require(openrac_mod_load(&api, nullptr) == 0 && replacements.size() == 5);
    api.version = "jp"; replacements.clear();
    require(openrac_mod_load(&api, nullptr) != 0 && replacements.empty());
    api.version = "ntsc";
    for (const char* point : {"Item_Give", "Item_Equip", "Planet_Unlock", "Vendor_BuildList", "Level_Load"}) {
        missing = point; failed.clear();
        require(openrac_mod_load(&api, nullptr) != 0 && failed.find(point) != std::string::npos);
    }
    openrac_mod_info info{}; openrac_mod_query(&info);
    require(std::string(info.id) == "aprac2-openrac-probe" && std::string(info.version) == "0.3.0");
    std::cout << "pass-through hooks, return values, disc guards and missing-hook failures passed\n";
}
