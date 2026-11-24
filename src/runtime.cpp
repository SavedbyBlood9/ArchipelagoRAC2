// SPDX-License-Identifier: MIT
// Native API adapter. Source facts and reward semantics come from APRac2 (MIT).
#include <algorithm>
#include <array>
#include <chrono>
#include <cstring>
#include <stdexcept>
#include "runtime.hpp"
#include "native_data.hpp"
#include "disc.hpp"

namespace rac2ap {
namespace {
Runtime* current=nullptr;
template<class F>void protect(F&& fn){try{fn();}catch(const std::exception& e){current->fault(e.what());}catch(...){current->fault("Unknown exception in native hook");}}
void hook_give(int32_t id){protect([&]{current->item_give(id);});}
int32_t hook_equip(int32_t id){int32_t result=0;protect([&]{result=current->item_equip(id);});return result;}
void hook_unlock(int32_t level){protect([&]{current->planet_unlock(level);});}
void hook_progress(){protect([]{current->collection_progress();});}
int32_t hook_platinum(){int32_t result=0;protect([&]{result=current->platinum_count();});return result;}
void hook_serialize(uint32_t out){protect([&]{current->serialize(out);});}
void hook_new_game(){protect([]{current->new_game();});}
void hook_kill(uint32_t moby,int32_t type){protect([&]{current->count_kill(moby,type);});}
void hook_vendor(int32_t hide){protect([&]{current->vendor(hide);});}
int32_t hook_price(){int32_t result=0;protect([&]{result=current->vendor_price();});return result;}
int32_t hook_extras(){int32_t result=0;protect([&]{result=current->extras_menu();});return result;}
static void(*original_levelup)(int32_t)=nullptr;
void hook_levelup(int32_t item){original_levelup(item);}
void frame(void*){try{current->tick();}catch(const std::exception& e){ /* tick reports its own errors */ (void)e;}}
void save_changed(void*){current->changed_save();}
struct Giver {const char* name; std::vector<int> items; bool parts; void(*original)(uint32_t)=nullptr; int mode=0; const char* signature="void(u32)";};
Giver givers[]={
    {"Moby_DynamoPickup_Update",{36},false}, {"Moby_TractorBeamSeller_Update",{46},false},
    {"Moby_BoxBreakerPickup_Update",{50},false}, {"Moby_ThermanatorSeller_Update",{39},false},
    {"Moby_ThermanatorArea_Update",{39},false}, {"Moby_SwingshotArea_Update",{13,20},false},
    {"Moby_GliderPickup_Update",{21},false}, {"Moby_LevitatorSeller_Update",{8},false},
    {"Moby_ChargeBootsRider_Update",{54},false}, {"Moby_RaceController_Update",{54},false},
    {"Moby_MapperReturn_Update",{5},false}, {"Moby_HypnomaticMaker_Update",{55},true},
    {"APRac2_EndakoRescue",{2,3},false},
    {"APRac2_TaboraWrench",{},false,nullptr,2},
    {"APRac2_PrisonWrench",{},false,nullptr,3},
    {"APRac2_TodanoTrader",{7},false,nullptr,4},
    {"APRac2_PrisonPlumber",{49},false,nullptr,5,"void(i32)"},
    {"APRac2_PrisonController",{},false,nullptr,6},
    {"APRac2_SiberiusThief",{},false,nullptr,7},
    {"APRac2_BoldanCutscene",{},false,nullptr,8},
    {"APRac2_HypnomaticPart",{},false,nullptr,9},
};
template<int N>void giver_hook(uint32_t moby){protect([&]{auto& g=givers[N];current->giver(g.original,moby,g.items,g.parts,g.mode);});}
void(*giver_callbacks[])(uint32_t)={giver_hook<0>,giver_hook<1>,giver_hook<2>,giver_hook<3>,giver_hook<4>,giver_hook<5>,
    giver_hook<6>,giver_hook<7>,giver_hook<8>,giver_hook<9>,giver_hook<10>,giver_hook<11>,
    giver_hook<12>,giver_hook<13>,giver_hook<14>,giver_hook<15>,giver_hook<16>,giver_hook<17>,giver_hook<18>,giver_hook<19>,giver_hook<20>};
}
Runtime::Runtime(const openrac_api* api,openrac_mod* mod,Bridge& bridge):api_(api),mod_(mod),bridge_(bridge),data_(json::parse(kNativeData)){
    for(auto& item:data_["items"]) items_[item["id"].get<int>()]=item;
    for(auto& row:data_["check_maps"]["INVENTORY_OFFSET_TO_LOCATION_ID"])
        item_locations_[row["game_value"].get<int>()]=row["location_id"].get<int>();
    for(auto& row:data_["direct_checks"]) if(row["vendor"].get<bool>())
        item_locations_[row["address"].get<int>()-0x1A7B30]=row["location"].get<int>();
    for(auto& row:data_["check_maps"]["PLANET_UNLOCK_TO_LOCATION_ID"])
        planet_locations_[row["game_value"].get<int>()]=row["location_id"].get<int>();
}
Runtime::~Runtime(){write8(0x1A7B51,0);}
void Runtime::fault(const std::string& reason){enabled_=false;error_=true;write8(0x1A7B51,0);status("ArchipelagoRAC2 stopped: "+reason);api_->play_travel(mod_,-1);}
uint32_t Runtime::address(const char* key)const{return data_["addresses"].at(key).get<uint32_t>();}
uint32_t Runtime::memory_address(uint32_t primary)const{return api_->relocate_data(disc_address(api_->version?api_->version:"ntsc",primary));}
uint8_t Runtime::read8(uint32_t addr)const{return api_->memory[memory_address(addr)];}
void Runtime::write8(uint32_t addr,uint8_t value){api_->memory[memory_address(addr)]=value;}
int32_t Runtime::read32(uint32_t addr)const{int32_t v;std::memcpy(&v,api_->memory+memory_address(addr),4);return v;}
void Runtime::write32(uint32_t addr,int32_t value){std::memcpy(api_->memory+memory_address(addr),&value,4);}
void Runtime::status(const std::string& text){if(text!=last_status_){api_->log(mod_,OPENRAC_LOG_INFO,text.c_str());last_status_=text;}}
void Runtime::checkpoint(){auto bytes=journal.serialize();if(api_->save_data_set(mod_,bytes.data(),static_cast<uint32_t>(bytes.size()))!=0)
    throw std::runtime_error("ArchipelagoRAC2 save checkpoint was refused");}
void Runtime::install(){
    current=this;
    auto take=[&](const char* name,const char* sig,void* replacement,void** original){
        if(api_->hook(mod_,name,sig,replacement,original)!=OPENRAC_HOOK_OK)
            throw std::runtime_error(std::string("ArchipelagoRAC2 native gameplay needs the custom-host hook: ")+name);
    };
    take("Item_Give","void(i32)",(void*)hook_give,(void**)&give_);
    take("Item_Equip","i32(i32)",(void*)hook_equip,(void**)&equip_);
    take("Planet_Unlock","void(i32)",(void*)hook_unlock,(void**)&unlock_);
    take("PlatinumBolts_CountTotal","i32()",(void*)hook_platinum,(void**)&platinum_);
    take("Hero_UpdateCollectionProgress","void()",(void*)hook_progress,(void**)&progress_);
    take("Save_Serialize","void(u32)",(void*)hook_serialize,(void**)&serialize_);
    take("Save_NewGame","void()",(void*)hook_new_game,(void**)&new_game_);
    take("APRac2_CountKill","void(u32,i32)",(void*)hook_kill,(void**)&kill_);
    take("Weapon_LevelUp","void(i32)",(void*)hook_levelup,(void**)&original_levelup);
    take("Vendor_BuildList","void(i32)",(void*)hook_vendor,(void**)&vendor_);
    take("Vendor_Price","i32()",(void*)hook_price,(void**)&price_);
    take("APRac2_ExtrasMenu","i32()",(void*)hook_extras,(void**)&extras_);
    levelup_=original_levelup;
    for(std::size_t i=0;i<std::size(givers);++i)
        take(givers[i].name,givers[i].signature,(void*)giver_callbacks[i],(void**)&givers[i].original);
    if(api_->on_save_data(mod_,save_changed,nullptr)!=0||api_->on_frame(mod_,frame,nullptr)!=0)
        throw std::runtime_error("ArchipelagoRAC2 save/frame callbacks could not be installed");
    changed_save();
}
void Runtime::changed_save(){
    write8(0x1A7B51,0);
    enabled_=false; error_=false; loads_=~0u; views_.clear();
    auto size=api_->save_data_get(mod_,nullptr,0);
    if(size>OPENRAC_SAVE_DATA_MAX){fault("Save metadata too large");return;}
    std::string bytes(size,'\0');
    if(size)api_->save_data_get(mod_,bytes.data(),size);
    try{journal.restore(bytes);}catch(const std::exception& e){fault(e.what());return;}
    // Clock zero comes only from the disc's unsaved New Game defaults (the source randomizer's gate).
    fresh_=!journal.initialized;
    for(int i=0;i<8;++i)if(read8(0x1A7360+i))fresh_=false;
}
void Runtime::new_game(){new_game_();enabled_=false;error_=false;journal=Journal{};fresh_=true;loads_=~0u;}
int Runtime::extras_menu(){return extras_();}
int Runtime::count(int item)const{return static_cast<int>(std::count(journal.applied.begin(),journal.applied.end(),item));}
void Runtime::view(uint32_t addr,uint8_t shown,int location){views_.push_back({addr,read8(addr),shown,location});write8(addr,shown);}
void Runtime::restore_views(std::size_t base){for(auto i=views_.size();i>base;--i)write8(views_[i-1].address,views_[i-1].real);views_.resize(base);}
void Runtime::giver(void(*original)(uint32_t),uint32_t moby,const std::vector<int>& items,bool parts,int mode){
    if(!enabled_){original(moby);return;}
    auto base=views_.size();
    for(int item:items){auto found=item_locations_.find(item);if(found!=item_locations_.end())view(address("inventory")+item,journal.checks.count(found->second)?1:0,found->second);}
    if(parts){int n=std::min(3,count(303));for(const char* key:{"hypnomatic_part1","hypnomatic_part2","hypnomatic_part3"})view(address(key),n-->0?1:0);}
    int wrench_location=mode==2?86:143;
    uint32_t wrench=address("weapon_subid_table")+10;
    if(mode==2||mode==3)view(wrench,journal.checks.count(wrench_location)?(mode==2?0x4A:0x4B):(mode==2?0x0A:0x4A),wrench_location);
    if(mode==5)view(address("inventory")+7,1); // Plumber is a check even without Armor Magnetizer.
    if(mode==6){view(address("inventory")+2,read8(address("inventory")+2));view(address("inventory")+3,read8(address("inventory")+3));}
    if(mode==9)view(address("inventory")+55,0); // A received Hypnomatic cannot hide its part pickup.
    int old_exit=read32(0x1A8B84);
    try{
        original(moby);
        for(auto i=base;i<views_.size();++i){const auto& v=views_[i];
            if(v.location>=0&&read8(v.address)>v.shown)check(v.location);
        }
        if((mode==2||mode==3)&&read8(wrench)!=(mode==2?0x0A:0x4A)&&!journal.checks.count(wrench_location))check(wrench_location);
        if(mode==4)write8(address("inventory")+49,count(14)?1:0); // Trading cannot consume AP progression.
        if(!old_exit&&read32(0x1A8B84)){
            if(mode==7&&read32(0x1B1680)==8)write32(0x1B1680,24);
            if(mode==8&&read32(0x1B1680)==14)write32(0x1A8B84,0);
        }
    }catch(...){restore_views(base);throw;}
    restore_views(base);
}
void Runtime::count_kill(uint32_t moby,int32_t type){
    if(!enabled_||!options_.value("enable_bolt_multiplier",0)){kill_(moby,type);return;}
    auto base=views_.size();view(0x1A7A0A,1);kill_(moby,type);restore_views(base);
}
void Runtime::serialize(uint32_t out){
    // Serializers nested in NPC updates must see the real AP inventory, then the NPC view resumes.
    // Direct-write pickups may save before their update returns. Capture their checks first.
    if(enabled_)for(const auto& v:views_)if(v.location>=0&&read8(v.address)>v.shown)check(v.location);
    for(auto i=views_.rbegin();i!=views_.rend();++i)write8(i->address,i->real);
    if(enabled_)try{checkpoint();}catch(const std::exception& e){fault(e.what());}
    serialize_(out);
    for(auto& v:views_)write8(v.address,v.shown);
}
void Runtime::check(int location){
    if(!active_locations_.count(location))return;
    if(journal.check(location,active_locations_)){checkpoint();publish();status("ArchipelagoRAC2 location checked: "+std::to_string(location));}
    for(const auto& item:item_locations_)if(item.second==location)write8(address("secondary_inventory")+item.first,1);
}
void Runtime::item_give(int id){
    if(giving_){give_(id);return;}
    if(!enabled_)return; // Opted-in campaigns cannot receive vanilla rewards before binding.
    auto location=item_locations_.find(id);
    if(location!=item_locations_.end()&&active_locations_.count(location->second)){check(location->second);return;}
    give_(id);
}
int Runtime::item_equip(int id){
    if(enabled_&&!giving_&&id>0&&id<56&&id!=10){
        bool owned=read8(address("inventory")+id)!=0;
        for(auto& v:views_)if(v.address==address("inventory")+id)owned=v.real!=0;
        if(!owned)return 0;
    }
    return equip_(id);
}
void Runtime::planet_unlock(int planet){
    if(!enabled_||giving_){unlock_(planet);return;}
    // Level setup's automatic unlock is not a coordinate transmission.
    if(planet==level_)return;
    auto loc=planet_locations_.find(planet);if(loc!=planet_locations_.end()){check(loc->second);return;}
    unlock_(planet);
}
int Runtime::platinum_count(){return enabled_?std::min(40,count(301)):platinum_();}
void Runtime::collection_progress(){
    if(!enabled_){progress_();return;}
    auto base=views_.size();int n=std::min(10,count(302));
    for(int i=0;i<10;++i)view(address("nanotech_boost_table")+i,i<n?1:0);
    progress_();restore_views(base);
}
void Runtime::give(int id){
    auto found=items_.find(id);if(found==items_.end())throw std::runtime_error("Unknown APRac2 item "+std::to_string(id));
    const auto& row=found->second;std::string kind=row["kind"];
    if(kind=="EquipmentData"||kind=="WeaponData"){
        int item=row["game_value"],base=item;
        if(row.contains("base_weapon_offset")&&!row["base_weapon_offset"].is_null())base=row["base_weapon_offset"];
        giving_=true;give_(base);giving_=false;
        if(base!=item&&read8(address("weapon_subid_table")+base)<item)write8(address("weapon_subid_table")+base,static_cast<uint8_t>(item));
        int ammo=row.value("max_ammo",0);if(ammo>0)write32(address("current_ammo_table")+base*4,ammo);
    }else if(kind=="CoordData"){
        int planet=row["game_value"];
        std::vector<int> planets{24};for(int i=0;i<25;++i){int v=read32(address("selectable_planets")+i*4);if(v>0&&v!=24&&v!=planet)planets.push_back(v);}
        planets.push_back(planet);if(planets.size()>25)throw std::runtime_error("Ship map exceeds capacity");
        for(int i=0;i<25;++i)write32(address("selectable_planets")+i*4,i<static_cast<int>(planets.size())?planets[i]:0);
        write8(address("highlighted_planets")+planet,10);
    }else if(id==304){
        if(count(id)<127){int64_t bolts=read32(address("current_bolts"));bolts+=std::max<int64_t>(bolts/5,10000);write32(address("current_bolts"),static_cast<int32_t>(std::min<int64_t>(bolts,0x7FFFFFFF)));}
    }else if(id==401){int n=std::min(2,count(id)+1);write8(address("weapon_subid_table")+10,n==1?0x4A:0x4B);
    }else if(id==402){write8(address("current_armor_level"),static_cast<uint8_t>(std::min(4,count(id)+1)));}
    // 301/302/303 are derived from the durable receipt history, never from location flags.
    if(api_->play_notice){std::string line="Received "+row["name"].get<std::string>();api_->play_notice(mod_,line.c_str());}
}
void Runtime::initialize(){
    std::fill(api_->memory+memory_address(address("inventory")),api_->memory+memory_address(address("inventory"))+56,0);
    std::fill(api_->memory+memory_address(address("secondary_inventory")),api_->memory+memory_address(address("secondary_inventory"))+56,0);
    for(int i=0;i<25;++i)write32(address("selectable_planets")+i*4,i==0?24:0);
    for(int i=0;i<8;++i)write32(address("quickselect")+i*4,0);
    write8(address("inventory")+4,1); // APRac2 always restores the Hydro-Pack/Clank support byte.
    write8(address("inventory")+10,1); // The base wrench is permanent, not a randomized receipt.
    checkpoint();
    if(level_!=24)api_->play_travel(mod_,24);
}
void Runtime::apply_options(){
    write8(0x1A7B51,169);write8(0x1A7B52,82);write8(0x1A7B53,50);
    write8(0x1A7B58,static_cast<uint8_t>(1|(options_.value("free_challenge_selection",0)?2:0)|(options_.value("no_revisit_reward_change",0)?4:0)));
    if(options_.value("skip_wupash_nebula",0))write8(address("wupash_complete_flag"),1);
    write8(address("easy_cutscene_skip"),1);
    for(auto& row:data_["addresses"]["cutscene_flags"]){uint32_t a=row[0];write8(a,read8(a)|row[1].get<int>());}
    uint32_t table=memory_address(0x239BA0u);
    if(options_.value("no_kill_reward_degradation",0)){
        uint32_t scale=memory_address(0x1A8858u);
        std::fill(api_->memory+scale,api_->memory+scale+32,100);
    }else if(options_.value("no_revisit_reward_change",0)){
        const uint8_t base[]={100,50,40,30,25,20,15,10};
        uint32_t scale=memory_address(0x1A8858u);
        for(int i=0;i<32;++i)api_->memory[scale+i]=base[i%8];
    }
    // These are relocated native addresses already; do not relocate the individual record again.
    int percentage=options_.value("weapon_xp_multiplier",100);
    double factor=1.0/(percentage*0.01);
    std::map<int,std::pair<int,int>> upgrades;
    for(auto it=data_["weapon_xp"]["0"].begin();it!=data_["weapon_xp"]["0"].end();++it)
        upgrades[std::stoi(it.key())]={static_cast<int>(it.value()[0].get<int>()*factor),it.value()[1].get<int>()};
    if(options_.value("extend_weapon_progression",0))for(auto it=data_["extended_pairs"].begin();it!=data_["extended_pairs"].end();++it){
        int tier2=std::stoi(it.key()),base=it.value()[0],tier3=it.value()[1];
        int required=static_cast<int>(0x600*factor);
        if(upgrades.count(base)&&upgrades.count(tier3)){
            required=upgrades[base].first+static_cast<int>(upgrades[tier3].first*0.5);
            upgrades[tier3].first+=required;
        }
        upgrades[tier2]={required,tier3};
    }
    for(auto& row:upgrades){
        int record=row.first,required=row.second.first,next=row.second.second;
        if(required>65535)throw std::runtime_error("Weapon XP requirement exceeds APRac2's 16-bit table");
        uint16_t xp=static_cast<uint16_t>(required);
        std::memcpy(api_->memory+table+record*0xE0+0x6C,&xp,2);api_->memory[table+record*0xE0+0x4A]=static_cast<uint8_t>(next);
    }
    percentage=options_.value("nanotech_xp_multiplier",100);
    factor=1.0/(percentage*0.01);
    for(std::size_t i=0;i<data_["nanotech_xp"].size();++i){uint16_t xp=static_cast<uint16_t>(data_["nanotech_xp"][i].get<int>()*factor);
        std::memcpy(api_->memory+table-0x310+4+4*i,&xp,2);}
}
void Runtime::vendor(int32_t hide){
    if(!enabled_){vendor_(hide);return;}
    const uint32_t root=memory_address(0x21F240u),list=root+0x140;
    auto get=[&](uint32_t a){int32_t v;std::memcpy(&v,api_->memory+a,4);return v;};
    auto put=[&](uint32_t a,int32_t v){std::memcpy(api_->memory+a,&v,4);};
    vendor_(hide);
    if(get(root+0x50)!=0)return; // Weapon vendors only; armor/mod/ship menus retain their code.
    bool megacorp=get(root+0x744)==0;
    std::string group=megacorp?"megacorp":"gadgetron";
    bool randomized=options_.value(megacorp?"randomize_megacorp_vendor":"randomize_gadgetron_vendor",0)!=0;
    using Entry=std::array<int32_t,6>;
    std::vector<Entry> ammo,weapons;
    auto read_entries=[&](bool want_ammo,std::vector<Entry>& into){
        int n=std::clamp(get(root+0x740),0,64);
        for(int i=0;i<n;++i){Entry entry;std::memcpy(entry.data(),api_->memory+list+i*0x18,0x18);
            if((entry[1]==1)==want_ammo)into.push_back(entry);}
    };
    read_entries(true,ammo);
    auto base=views_.size();
    for(auto& row:data_["vendors"][group])view(address("inventory")+row["item"].get<int>(),journal.checks.count(row["location"].get<int>())?1:0);
    vendor_(hide);read_entries(false,weapons);restore_views(base);
    if(randomized){
        weapons.clear();
        for(auto& row:data_["vendors"][group]){
            int location=row["location"],item=row["item"];
            if(journal.checks.count(location)||!active_locations_.count(location))continue;
            if(megacorp&&!journal.visited.count(row["planet"].get<int>()))continue;
            int model=0x47;
            auto scout=scouts_.find(std::to_string(location));
            if(scout!=scouts_.end()&&scout->value("player",0)==identity_.value("slot",0)){
                auto reward=items_.find(scout->value("item",-1));
                if(reward!=items_.end())model=reward->second.value("oclass_id",0x47);
            }
            weapons.push_back({item,0,model,0,0,0});
        }
    }
    std::vector<Entry> entries;
    if(randomized){entries=vendor_ammo_?ammo:weapons;if(entries.empty())entries=ammo;}
    else{entries=weapons;entries.insert(entries.end(),ammo.begin(),ammo.end());}
    if(entries.size()>64)throw std::runtime_error("ArchipelagoRAC2 vendor list exceeds native capacity");
    for(std::size_t i=0;i<entries.size();++i)std::memcpy(api_->memory+list+i*0x18,entries[i].data(),0x18);
    put(root+0x740,static_cast<int32_t>(entries.size()));
    put(root+0x80,std::clamp(get(root+0x80),0,std::max(0,static_cast<int>(entries.size())-1)));
}
int Runtime::vendor_price(){
    if(!enabled_)return price_();
    const uint32_t root=memory_address(0x21F240u);
    int cursor;std::memcpy(&cursor,api_->memory+root+0x80,4);
    int size;std::memcpy(&size,api_->memory+root+0x740,4);
    if(cursor<0||cursor>=size||size>64)return price_();
    std::array<int32_t,6> row;std::memcpy(row.data(),api_->memory+root+0x140+cursor*24,24);
    int item=row[0];
    if(row[1]!=0||row[4]!=0||row[5]!=0||!item_locations_.count(item)||!active_locations_.count(item_locations_.at(item)))return price_();
    auto base=views_.size();view(address("weapon_subid_table")+item,static_cast<uint8_t>(item));
    int result=price_();restore_views(base);return result;
}
void Runtime::progression(){
    if(!options_.value("extend_weapon_progression",0))return;
    int decoy=read32(address("current_ammo_table")+0x11*4);
    if(decoy_ammo_>=0&&decoy<decoy_ammo_)write32(address("current_weapon_xp_table")+0x11*4,read32(address("current_weapon_xp_table")+0x11*4)+0x180);
    decoy_ammo_=decoy;
    int pending=read32(address("current_weapon_xp_table")+0x31*4);
    if(pending>0){write32(address("current_weapon_xp_table")+0x31*4,0);
        if(read32(address("equipped_weapon"))==0x35)write32(address("current_weapon_xp_table")+0x35*4,read32(address("current_weapon_xp_table")+0x35*4)+pending);}
    uint32_t table=memory_address(0x239BA0u);
    std::set<int> weapons;
    for(const auto& entry:items_)if(entry.second["kind"]=="WeaponData"){
        const auto& row=entry.second;
        int item=row["game_value"];
        if(row.contains("base_weapon_offset")&&!row["base_weapon_offset"].is_null())item=row["base_weapon_offset"];
        weapons.insert(item);
    }
    for(int item:weapons)if(item<56&&read8(address("inventory")+item))for(int step=0;step<4;++step){
        int record=read8(address("weapon_subid_table")+item);if(record<=0||record>0xFF)break;
        uint16_t threshold;std::memcpy(&threshold,api_->memory+table+record*0xE0+0x6C,2);
        uint16_t next;std::memcpy(&next,api_->memory+table+record*0xE0+0x4A,2);
        if(!next||threshold<=0||read32(address("current_weapon_xp_table")+item*4)/32<threshold)break;
        levelup_(item);if(read8(address("weapon_subid_table")+item)==record)break;
    }
}
void Runtime::deaths(const json& state,const openrac_play_status& st){
    if(!options_.value("death_link",0))return;
    bool alive=read32(address("current_nanotech"))>0;
    if(alive&&remote_death_)remote_death_=false;
    if(alive&&st.phase==OPENRAC_PLAY_PLAYING&&state.contains("death_events"))for(auto& event:state["death_events"]){
        double stamp=event.at("time");if(journal.deaths.insert(stamp).second){checkpoint();write32(address("current_nanotech"),0);remote_death_=true;alive=false;break;}
    }
    if(was_alive_&&!alive&&!remote_death_)bridge_.send(json{{"type","death"},{"identity",identity_},{"event_id",std::to_string(std::chrono::system_clock::now().time_since_epoch().count())+":"+std::to_string(++death_id_)}});
    was_alive_=alive;
}
void Runtime::receive(const json& state){
    std::vector<int> items;for(auto& row:state.at("items"))items.push_back(row.at("item"));
    journal.receive(items,[&](int id){give(id);},[&](const std::string&){checkpoint();});
}
void Runtime::scan(){
    for(const auto& pair:std::vector<std::pair<const char*,const char*>>{{"PLAT_BOLT_OFFSET_TO_LOCATION_ID","platinum_bolt_table"},{"NANOTECH_OFFSET_TO_LOCATION_ID","nanotech_boost_table"}})
        for(auto& row:data_["check_maps"][pair.first])if(read8(address(pair.second)+row["game_value"].get<int>()))check(row["location_id"]);
    for(auto& row:data_["direct_checks"]){if(row["vendor"].get<bool>())continue;if(read8(row["address"]))check(row["location"]);}
    if(level_==3){for(int item:{2,3,20}){
        if(read8(address("inventory")+item)){
            int apid=0;for(auto& entry:items_)if(entry.second.value("game_value",-1)==item&&entry.second["kind"]=="EquipmentData")apid=entry.first;
            if(apid&&!count(apid)){write8(address("inventory")+item,0);write8(address("secondary_inventory")+item,0);check(item_locations_.at(item));}
        }
    }}
    // Native moby state and key use the same UID/state facts as APRac2's goal detector.
    if(level_==20&&!journal.goal){openrac_moby mobys[2048]{};for(auto& moby:mobys)moby.size=sizeof moby;
        int n=api_->moby_list(mobys,2048);for(int i=0;i<std::min(n,2048);++i)if(mobys[i].key==197&&mobys[i].state==0x11){journal.goal=true;checkpoint();publish();}}
}
void Runtime::publish(){
    if(!enabled_)return;
    bridge_.send(json{{"type","checks"},{"identity",identity_},{"locations",journal.checks},
        {"received",journal.cursor},{"bolts",read32(address("current_bolts"))},
        {"platinum",std::min(40,count(301))},{"nanotech_boosts",std::min(10,count(302))},
        {"native_flags",read8(0x1A7B58)},{"level",level_}});
    if(journal.goal)bridge_.send(json{{"type","goal"},{"identity",identity_}});
}
void Runtime::tick(){openrac_play_status st{};st.size=sizeof st;if(api_->play_status(&st)==0)step(bridge_.snapshot(),st);}
void Runtime::step(const json& state,const openrac_play_status& st){
    try{
        ++frames_;if(error_)return;
        level_=st.level;
        if(state.is_null()||!state.value("connected",false)||!state.value("synced",false)){
            if(!enabled_&&st.level>=0&&st.phase==OPENRAC_PLAY_PLAYING){
                status("ArchipelagoRAC2: connect and synchronize the sidecar before starting or loading a campaign");
                api_->play_travel(mod_,-1);
            }
            if(enabled_&&st.level>=0&&(st.phase==OPENRAC_PLAY_PLAYING||st.phase==OPENRAC_PLAY_MENU)){
                if(st.loads!=loads_){loads_=st.loads;apply_options();}scan();
                status("ArchipelagoRAC2: offline; collected checks retained for reconnection");
            }
            return;
        }
        if(st.level<0||st.phase==OPENRAC_PLAY_LOADING)return;
        if(!enabled_){
            options_=state.at("options");identity_=state.at("identity");
            active_locations_=options_["openrac"]["active_locations"].get<std::set<int>>();
            bool initializing=!journal.initialized;journal.bind(identity_,fresh_);enabled_=true;
            if(initializing){
                initialize();fresh_=false;
                for(const auto& event:state.value("death_events",json::array()))journal.deaths.insert(event.at("time").get<double>());
                checkpoint();
            }
            status("ArchipelagoRAC2: native rewards and save tracking active (experimental)");publish();
        }
        if(state.at("identity")!=identity_)throw std::runtime_error("ArchipelagoRAC2 server identity changed during play");
        scouts_=state.value("scouts",json::object());
        if(st.loads!=loads_){loads_=st.loads;if(journal.visited.insert(level_).second)checkpoint();apply_options();}
        if(st.phase==OPENRAC_PLAY_PLAYING||st.phase==OPENRAC_PLAY_MENU){receive(state);scan();progression();deaths(state,st);
            // Original secondary inventory represents collected locations, never received ownership.
            for(const auto& item:item_locations_)write8(address("secondary_inventory")+item.first,journal.checks.count(item.second)?1:0);
            write8(address("clank_disabled"),0);write8(address("inventory")+4,1);
            write8(address("inventory")+2,count(1)?1:0);write8(address("inventory")+3,count(2)?1:0);
            write8(address("inventory")+54,count(17)?1:0);
        }
        if((read32(address("controller_input"))&0xFFFF)==0x10F)api_->play_travel(mod_,24);
        if(read32(0x1A8BB0)==5){int buttons=read32(address("controller_input"))&0xFFFF;
            bool mode=vendor_ammo_;if(buttons==0x4000)vendor_ammo_=true;if(buttons==0x1000)vendor_ammo_=false;
            if(mode!=vendor_ammo_)vendor(0);
        }else vendor_ammo_=false;
        if(frames_%120==0)publish();
    }catch(const std::exception& e){fault(e.what());throw;}
}
}
