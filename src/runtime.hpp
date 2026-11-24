// SPDX-License-Identifier: MIT
#pragma once
#include <map>
#include <set>
#include <string>
#include <vector>
#include "openrac/openrac_mod.h"
#include "bridge.hpp"
#include "journal.hpp"

namespace rac2ap {
class Runtime {
public:
    Runtime(const openrac_api* api,openrac_mod* mod,Bridge& bridge);
    ~Runtime();
    void fault(const std::string& reason);
    void install();
    void tick();
    void step(const json& state,const openrac_play_status& status);
    void changed_save();
    void item_give(int id);
    int item_equip(int id);
    void planet_unlock(int level);
    void collection_progress();
    int platinum_count();
    void serialize(unsigned out);
    void new_game();
    void giver(void(*original)(uint32_t),uint32_t moby,const std::vector<int>& items,bool parts=false,int mode=0);
    void count_kill(uint32_t moby,int32_t type);
    void vendor(int32_t hide_unowned);
    int vendor_price();
    int extras_menu();
    Journal journal;
    bool active() const { return enabled_; }
private:
    const openrac_api* api_;
    openrac_mod* mod_;
    Bridge& bridge_;
    json data_,options_,identity_;
    bool enabled_=false, fresh_=false, giving_=false, error_=false;
    unsigned loads_=~0u,frames_=0;
    int level_=-1;
    std::string last_status_;
    std::set<int> active_locations_;
    std::map<int,json> items_;
    std::map<int,int> item_locations_,planet_locations_;
    struct View { uint32_t address; uint8_t real,shown; int location; };
    std::vector<View> views_;
    void (*give_)(int32_t)=nullptr;
    int32_t (*equip_)(int32_t)=nullptr;
    void (*unlock_)(int32_t)=nullptr;
    void (*progress_)(void)=nullptr;
    int32_t (*platinum_)(void)=nullptr;
    void (*serialize_)(uint32_t)=nullptr;
    void (*new_game_)(void)=nullptr;
    void (*kill_)(uint32_t,int32_t)=nullptr;
    void (*levelup_)(int32_t)=nullptr;
    int decoy_ammo_=-1;
    std::set<double> seen_deaths_;
    bool was_alive_=true,remote_death_=false;
    unsigned death_id_=0;
    void (*vendor_)(int32_t)=nullptr;
    int32_t (*price_)(void)=nullptr;
    int32_t (*extras_)(void)=nullptr;
    bool vendor_ammo_=false;
    json scouts_;
    uint32_t address(const char* key) const;
    uint32_t memory_address(uint32_t primary) const;
    uint8_t read8(uint32_t addr) const;
    void write8(uint32_t addr,uint8_t value);
    int32_t read32(uint32_t addr) const;
    void write32(uint32_t addr,int32_t value);
    void checkpoint();
    void status(const std::string& text);
    int count(int item) const;
    void give(int item);
    void check(int location);
    void receive(const json& state);
    void scan();
    void initialize();
    void apply_options();
    void publish();
    void progression();
    void deaths(const json& state,const openrac_play_status& status);
    void view(uint32_t addr,uint8_t shown,int location=-1);
    void restore_views(std::size_t base);
};
}
