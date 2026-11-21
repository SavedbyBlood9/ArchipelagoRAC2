#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <winsock2.h>
#include <ws2tcpip.h>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <thread>
#include "bridge.hpp"
void require(bool result) { if (!result) { std::cerr<<"bridge assertion failed\n"; std::exit(1); } }
int main() {
    WSADATA data{}; require(WSAStartup(MAKEWORD(2,2),&data)==0);
    SOCKET server=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP); require(server!=INVALID_SOCKET);
    sockaddr_in address{}; address.sin_family=AF_INET;
    inet_pton(AF_INET,"127.0.0.1",&address.sin_addr);
    require(bind(server,reinterpret_cast<sockaddr*>(&address),sizeof address)==0);
    int size=sizeof address; getsockname(server,reinterpret_cast<sockaddr*>(&address),&size);
    require(listen(server,1)==0);
    rac2ap::Bridge bridge; bridge.start(ntohs(address.sin_port),"test-token-0123456789");
    fd_set reads; FD_ZERO(&reads); FD_SET(server,&reads); timeval timeout{3,0};
    require(select(0,&reads,nullptr,nullptr,&timeout)>0);
    SOCKET peer=accept(server,nullptr,nullptr); require(peer!=INVALID_SOCKET);
    DWORD receive_timeout=2000;
    setsockopt(peer,SOL_SOCKET,SO_RCVTIMEO,reinterpret_cast<const char*>(&receive_timeout),sizeof receive_timeout);
    std::string hello; char bytes[256];
    while (hello.find('\n')==std::string::npos) { int n=recv(peer,bytes,sizeof bytes,0); require(n>0); hello.append(bytes,n); }
    auto packet=nlohmann::json::parse(hello);
    require(packet["token"]=="test-token-0123456789" && packet["type"]=="hello");
    // Ignore a malformed type; accept a valid packet assembled across TCP chunks.
    std::string first="{\"type\":123}\n{\"type\":\"state\",\"synced\":";
    std::string second="true,\"items\":[{\"item\":10}]}\n";
    require(send(peer,first.data(),static_cast<int>(first.size()),0)>0);
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    require(send(peer,second.data(),static_cast<int>(second.size()),0)>0);
    bool found=false;
    for (int i=0;i<100;++i) {
        auto state=bridge.snapshot();
        if (!state.is_null() && state.value("synced",false)) { found=state["items"][0]["item"]==10; break; }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    require(found);
    require(bridge.send(nlohmann::json{{"type","checks"},{"locations",{10,32}}}));
    std::string event;
    while(event.find('\n')==std::string::npos){int n=recv(peer,bytes,sizeof bytes,0);require(n>0);event.append(bytes,n);}
    auto received=nlohmann::json::parse(event);require(received["type"]=="checks"&&received["locations"].size()==2);
    bridge.stop(); closesocket(peer); closesocket(server); WSACleanup();
    std::cout<<"native loopback authentication, split packets and clean shutdown passed\n";
}
