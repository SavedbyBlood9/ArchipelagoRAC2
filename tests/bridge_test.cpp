#include <chrono>
#include <cstdlib>
#include <iostream>
#include <thread>
#include "bridge.hpp"
#include "net.hpp"
using namespace rac2ap;
void require(bool result) { if (!result) { std::cerr<<"bridge assertion failed\n"; std::exit(1); } }
int main() {
    require(net::startup());
    net::socket_t server=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP); require(server!=net::invalid);
    sockaddr_in address{}; address.sin_family=AF_INET;
    inet_pton(AF_INET,"127.0.0.1",&address.sin_addr);
    require(bind(server,reinterpret_cast<sockaddr*>(&address),sizeof address)==0);
    net::socklen size=sizeof address; getsockname(server,reinterpret_cast<sockaddr*>(&address),&size);
    require(listen(server,1)==0);
    rac2ap::Bridge bridge; bridge.start(ntohs(address.sin_port),"test-token-0123456789");
    fd_set reads; FD_ZERO(&reads); FD_SET(server,&reads); timeval timeout{3,0};
    require(select(net::nfds(server),&reads,nullptr,nullptr,&timeout)>0);
    net::socket_t peer=accept(server,nullptr,nullptr); require(peer!=net::invalid);
    net::set_recv_timeout_ms(peer,2000);
    std::string hello; char bytes[256];
    while (hello.find('\n')==std::string::npos) { int n=static_cast<int>(recv(peer,bytes,sizeof bytes,0)); require(n>0); hello.append(bytes,n); }
    auto packet=nlohmann::json::parse(hello);
    require(packet["token"]=="test-token-0123456789" && packet["type"]=="hello");
    // Ignore a malformed type; accept a valid packet assembled across TCP chunks.
    std::string first="{\"type\":123}\n{\"type\":\"state\",\"synced\":";
    std::string second="true,\"items\":[{\"item\":10}]}\n";
    require(net::send(peer,first.data(),first.size())>0);
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    require(net::send(peer,second.data(),second.size())>0);
    bool found=false;
    for (int i=0;i<100;++i) {
        auto state=bridge.snapshot();
        if (!state.is_null() && state.value("synced",false)) { found=state["items"][0]["item"]==10; break; }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    require(found);
    require(bridge.send(nlohmann::json{{"type","checks"},{"locations",{10,32}}}));
    std::string event;
    while(event.find('\n')==std::string::npos){int n=static_cast<int>(recv(peer,bytes,sizeof bytes,0));require(n>0);event.append(bytes,n);}
    auto received=nlohmann::json::parse(event);require(received["type"]=="checks"&&received["locations"].size()==2);
    bridge.stop(); net::close(peer); net::close(server); net::cleanup();
    std::cout<<"native loopback authentication, split packets and clean shutdown passed\n";
}
