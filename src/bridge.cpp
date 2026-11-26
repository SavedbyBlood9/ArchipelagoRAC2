// SPDX-License-Identifier: MIT
// The worker speaks only to the local sidecar; all OpenRAC SDK calls stay on the game thread.
#include <chrono>
#include "bridge.hpp"
#include "net.hpp"

namespace rac2ap {
using namespace std::chrono_literals;
Bridge::~Bridge() { stop(); }
void Bridge::start(int port, std::string token) {
    stop(); running_ = true;
    thread_ = std::thread([this,port,token] { run(port,token); });
}
void Bridge::stop() { running_ = false; if (thread_.joinable()) thread_.join(); }
nlohmann::json Bridge::snapshot() { std::lock_guard<std::mutex> guard(mutex_); return state_; }
bool Bridge::send(const nlohmann::json& event) {
    auto text=event.dump()+"\n";
    if(text.size()>1024*1024) return false;
    std::lock_guard<std::mutex> guard(mutex_);
    if(outgoing_.size()>=256) return false;
    outgoing_.push_back(std::move(text)); return true;
}
void Bridge::run(int port, const std::string& token) {
    if (!net::startup()) return;
    while (running_) {
        net::socket_t sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (sock == net::invalid) break;
        net::set_nonblocking(sock);
        sockaddr_in addr{}; addr.sin_family = AF_INET; addr.sin_port = htons(static_cast<unsigned short>(port));
        inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
        int result = connect(sock, reinterpret_cast<sockaddr*>(&addr), sizeof addr);
        bool connected = result == 0;
        if (!connected && net::connecting()) {
            fd_set writes, errors; FD_ZERO(&writes); FD_ZERO(&errors); FD_SET(sock,&writes); FD_SET(sock,&errors);
            timeval timeout{0,250000};
            if (select(net::nfds(sock),nullptr,&writes,&errors,&timeout)>0 && FD_ISSET(sock,&writes) && !FD_ISSET(sock,&errors)) {
                int error=0; net::socklen size=sizeof error;
                getsockopt(sock,SOL_SOCKET,SO_ERROR,reinterpret_cast<char*>(&error),&size);
                connected = error == 0;
            }
        }
        if (connected && running_) {
            auto hello = nlohmann::json{{"type","hello"},{"token",token}}.dump() + "\n";
            std::size_t sent=0;
            while (running_ && sent<hello.size()) {
                int n = net::send(sock,hello.data()+sent,hello.size()-sent);
                if (n>0) sent+=n;
                else if (net::would_block()) std::this_thread::sleep_for(10ms);
                else break;
            }
            std::string buffer;
            std::string outgoing;
            std::size_t offset=0;
            while (running_ && sent==hello.size()) {
                if(outgoing.empty()) {
                    std::lock_guard<std::mutex> guard(mutex_);
                    if(!outgoing_.empty()) { outgoing=std::move(outgoing_.front()); outgoing_.pop_front(); offset=0; }
                }
                if(!outgoing.empty()) {
                    int written=net::send(sock,outgoing.data()+offset,outgoing.size()-offset);
                    if(written>0) { offset+=written; if(offset==outgoing.size()) outgoing.clear(); }
                    else if(!net::would_block()) break;
                }
                fd_set reads; FD_ZERO(&reads); FD_SET(sock,&reads); timeval timeout{0,100000};
                int ready = select(net::nfds(sock),&reads,nullptr,nullptr,&timeout);
                if (ready<0) break;
                if (!ready) continue;
                char bytes[8192]; int n=static_cast<int>(recv(sock,bytes,sizeof bytes,0));
                if (n<=0) break;
                buffer.append(bytes,n);
                if (buffer.size()>1024*1024) break;
                std::size_t end;
                while ((end=buffer.find('\n'))!=std::string::npos) {
                    auto packet = nlohmann::json::parse(buffer.substr(0,end),nullptr,false);
                    buffer.erase(0,end+1);
                    if (!packet.is_discarded() && packet.is_object() && packet.contains("type")
                        && packet["type"].is_string() && packet["type"]=="state") {
                        std::lock_guard<std::mutex> guard(mutex_); state_=std::move(packet);
                    }
                }
            }
        }
        net::close(sock);
        { std::lock_guard<std::mutex> guard(mutex_); state_=nullptr; }
        for (int i=0; running_ && i<10; ++i) std::this_thread::sleep_for(100ms);
    }
    net::cleanup();
}
}
