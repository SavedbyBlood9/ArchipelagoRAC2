#include <cstdlib>
#include <iostream>
#include "journal.hpp"
using rac2ap::json;
void require(bool result) { if (!result) std::exit(1); }
template<class F> void rejects(F f) { bool threw=false; try{f();}catch(const std::exception&){threw=true;} require(threw); }
int main() {
    rac2ap::Journal save;
    json identity={{"seed","test"},{"team",0},{"slot",1}};
    rejects([&]{save.bind(identity,false);});
    save.bind(identity,true);
    int bolts=0, gadgets=0;
    std::string checkpoint;
    auto give=[&](int item){if(item==304) bolts+=10000;else ++gadgets;};
    auto store=[&](const std::string& bytes){checkpoint=bytes;};
    save.receive({10,304},give,store);
    save.receive({10,304},give,store);
    require(bolts==10000 && gadgets==1 && save.cursor==2);
    auto earlier=checkpoint;
    save.receive({10,304,304},give,store); require(bolts==20000);
    // A rollback brings back both the game state and this earlier cursor.
    bolts=10000; save.restore(earlier); save.bind(identity,false);
    save.receive({10,304,304},give,store); require(bolts==20000);
    require(save.check(10,{10,11})); require(!save.check(10,{10,11}));
    rejects([&]{save.check(12,{10,11});});
    rejects([&]{save.bind(json{{"seed","other"},{"team",0},{"slot",1}},false);});
    rejects([&]{save.receive({10,301,304},give,store);});
    require(bolts==20000);
    std::cout<<"item replay, save rollback, disabled checks and seed binding passed\n";
}
