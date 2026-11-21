// A native host simulator: invokes the actual adapter and registered SDK replacements.
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <vector>
#include "runtime.hpp"
using rac2ap::json;
static std::vector<uint8_t> memory(32*1024*1024);
static std::map<std::string,void*> hooks;
static std::string metadata;
static int coins_seen=-1,saved_dynamo=-1,travel=-1,grants=0;
static int kill_flag=-1;
static bool victory=false;
void require(bool b){if(!b){std::cerr<<"native runtime assertion failed\n";std::exit(1);}}
uint32_t relocate(uint32_t a){return a;}
void log_line(openrac_mod*,int,const char* text){std::cout<<text<<"\n";}
void original_give(int32_t id){++grants;memory[0x1A7AF8+id]=1;}
int32_t original_equip(int32_t id){return id;}
void original_unlock(int32_t){}
void original_progress(){coins_seen=0;for(int i=0;i<10;++i)coins_seen+=memory[0x1A7A28+i]!=0;}
int32_t original_platinum(){return 40;}
void original_serialize(uint32_t){saved_dynamo=memory[0x1A7AF8+36];}
void original_newgame(){}
void original_giver(uint32_t){}
void original_kill(uint32_t,int32_t){kill_flag=memory[0x1A7A0A];}
void original_level(int32_t){}
int32_t original_extras(){return 0;}
int32_t original_price(){return memory[0x139568+22]*100;}
void original_vendor(int32_t){
    const uint32_t root=0x21F240,list=root+0x140;int32_t n=0;
    for(int item:{22,26}){
        int32_t entry[6]={item,memory[0x1A7AF8+item]?1:0,0xCDB,0,0,0};
        std::memcpy(memory.data()+list+n++*24,entry,24);
    }
    std::memcpy(memory.data()+root+0x740,&n,4);
}
int hook(openrac_mod*,const char* name,const char*,void* fn,void** original){
    hooks[name]=fn;std::string n=name;
    if(n=="Item_Give")*original=(void*)original_give;
    else if(n=="Item_Equip")*original=(void*)original_equip;
    else if(n=="Planet_Unlock")*original=(void*)original_unlock;
    else if(n=="Hero_UpdateCollectionProgress")*original=(void*)original_progress;
    else if(n=="PlatinumBolts_CountTotal")*original=(void*)original_platinum;
    else if(n=="Save_Serialize")*original=(void*)original_serialize;
    else if(n=="Save_NewGame")*original=(void*)original_newgame;
    else if(n=="APRac2_CountKill")*original=(void*)original_kill;
    else if(n=="Vendor_BuildList")*original=(void*)original_vendor;
    else if(n=="Vendor_Price")*original=(void*)original_price;
    else if(n=="Weapon_LevelUp")*original=(void*)original_level;
    else if(n=="APRac2_ExtrasMenu")*original=(void*)original_extras;
    else *original=(void*)original_giver;
    return 0;
}
int frame_callback(openrac_mod*,openrac_frame_fn,void*){return 0;}
uint32_t save_get(openrac_mod*,void* out,uint32_t size){if(out&&size>=metadata.size())std::memcpy(out,metadata.data(),metadata.size());return static_cast<uint32_t>(metadata.size());}
int save_set(openrac_mod*,const void* bytes,uint32_t size){metadata.assign(static_cast<const char*>(bytes),size);return 0;}
int go(openrac_mod*,int level){travel=level;return 0;}
int mobys(openrac_moby* out,int){if(!victory)return 0;out[0].key=197;out[0].state=0x11;return 1;}
void npc_pickup(uint32_t){
    require(memory[0x1A7AF8+36]==0); // Received elsewhere does not consume this location.
    ((void(*)(int32_t))hooks.at("Item_Give"))(36);
    ((void(*)(uint32_t))hooks.at("Save_Serialize"))(0);
}
void clank_rescue(uint32_t){memory[0x1A7AF8+2]=1;memory[0x1A7AF8+3]=1;((void(*)(uint32_t))hooks["Save_Serialize"])(0);}
void wrench_pickup(uint32_t){memory[0x139568+10]=0x4A;((void(*)(uint32_t))hooks["Save_Serialize"])(0);}
int word(uint32_t addr){int32_t v;std::memcpy(&v,memory.data()+addr,4);return v;}
int half(uint32_t addr){uint16_t v;std::memcpy(&v,memory.data()+addr,2);return v;}
int bolts(){int32_t n;std::memcpy(&n,memory.data()+0x1A79F8,4);return n;}
int main(){
    openrac_api api{};api.size=sizeof api;api.api_major=1;api.api_minor=19;api.memory=memory.data();
    api.relocate_data=relocate;api.log=log_line;api.hook=hook;api.on_frame=frame_callback;api.on_save_data=frame_callback;
    api.save_data_get=save_get;api.save_data_set=save_set;api.play_travel=go;api.moby_list=mobys;
    rac2ap::Bridge bridge;rac2ap::Runtime game(&api,nullptr,bridge);game.install();
    json identity={{"seed","seed"},{"team",0},{"slot",1}};
    json options={{"skip_wupash_nebula",1},{"nanotech_xp_multiplier",600},{"weapon_xp_multiplier",30},
                  {"extend_weapon_progression",1},{"death_link",1},
                  {"enable_bolt_multiplier",1},{"no_kill_reward_degradation",1},{"no_revisit_reward_change",1},
                  {"free_challenge_selection",1},{"first_person_mode_glitch_in_logic",3},
                  {"randomize_megacorp_vendor",1},{"randomize_gadgetron_vendor",1},
                  {"openrac",{{"active_locations",{10,12,13,14,32,33,31,86,143,180,300,301}}}}};
    json state={{"connected",true},{"synced",true},{"identity",identity},{"options",options},
                {"items",json::array({{{"item",10}},{{"item",304}},{{"item",301}},{{"item",302}},{{"item",303}},{{"item",401}}})}};
    openrac_play_status status{};status.size=sizeof status;status.level=24;status.phase=OPENRAC_PLAY_PLAYING;status.loads=1;
    game.step(state,status);require(game.active());require(memory[0x1A7AF8+36]==1);require(bolts()==10000);
    require(memory[0x1A7B30+36]==0); // Received ownership must not mark its physical pickup.
    require(memory[0x1A7AF8+10]==1&&game.item_equip(10)==10);
    require(half(0x239BA0+22*0xE0+0x6C)==1333&&half(0x239BA0-0x310+4)==30);
    require(game.journal.cursor==6);game.step(state,status);require(bolts()==10000);
    require(((int(*)())hooks["PlatinumBolts_CountTotal"])()==1);
    memory[0x1A7A28+4]=1;memory[0x1A7A28+5]=1;
    ((void(*)())hooks["Hero_UpdateCollectionProgress"])();require(coins_seen==1);
    require(memory[0x1A7A28+4]==1&&memory[0x1A7A28+5]==1);
    game.giver(npc_pickup,0,{36});require(game.journal.checks.count(10));require(saved_dynamo==1);
    require(memory[0x1A7B30+36]==1);
    require(memory[0x1A7AF8+36]==1);
    game.giver(clank_rescue,0,{2,3});require(game.journal.checks.count(32)&&game.journal.checks.count(33));
    require(memory[0x1A7AF8+2]==0&&memory[0x1A7AF8+3]==0);
    game.journal.checks.erase(32);game.journal.checks.erase(33);
    game.giver(clank_rescue,0,{},false,6); // Prison restores are not Endako pickups, even across a save.
    require(!game.journal.checks.count(32)&&!game.journal.checks.count(33));
    memory[0x139568+10]=0x4B;game.giver(wrench_pickup,0,{},false,2);
    require(game.journal.checks.count(86)&&memory[0x139568+10]==0x4B);
    require(memory[0x1A7B58]==7);
    game.count_kill(0,0);require(kill_flag==1&&memory[0x1A7A0A]==0);
    for(int i=0;i<32;++i)require(memory[0x1A8858+i]==100);
    game.journal.visited.insert(1);memory[0x1A7AF8+22]=1;
    game.vendor(0);require(word(0x21F240+0x740)==2);
    require(word(0x21F240+0x140)==22&&word(0x21F240+0x144)==0);
    memory[0x139568+22]=0x40;require(game.vendor_price()==2200&&memory[0x139568+22]==0x40);
    game.item_give(22);game.vendor(0);require(word(0x21F240+0x740)==1);
    require(word(0x21F240+0x140)==26); // Ownership did not hide its independent purchase check.
    auto saved=metadata;
    state["items"].push_back({{"item",304}});game.step(state,status);require(bolts()==20000);
    // SDK restore loads both original game memory and its matching mod metadata.
    metadata=saved;int32_t old=10000;std::memcpy(memory.data()+0x1A79F8,&old,4);game.changed_save();
    game.step(state,status);require(bolts()==20000&&game.journal.cursor==7);
    state["connected"]=false;game.step(state,status);require(game.active());
    state["connected"]=true;int health=10;std::memcpy(memory.data()+0x18C2EC,&health,4);
    state["death_events"]=json::array({{{"time",123.0}}});game.step(state,status);
    require(word(0x18C2EC)==0&&game.journal.deaths.count(123.0));
    std::memcpy(memory.data()+0x18C2EC,&health,4);game.step(state,status);require(word(0x18C2EC)==10);
    status.level=20;victory=true;game.step(state,status);require(game.journal.goal);
    state["connected"]=true;state["identity"]["seed"]="foreign";
    bool rejected=false;try{game.step(state,status);}catch(const std::exception&){rejected=true;}
    require(rejected&&!game.active());int before=grants;game.item_give(36);require(grants==before);
    std::cout<<"actual adapter: receipts, currency, virtual counts, NPC saves, rollback and foreign saves passed\n";
}

