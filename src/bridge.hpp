// SPDX-License-Identifier: MIT
#pragma once
#include <atomic>
#include <mutex>
#include <string>
#include <thread>
#include <deque>
#include "json.hpp"

namespace rac2ap {
class Bridge {
public:
    ~Bridge();
    void start(int port, std::string token);
    void stop();
    nlohmann::json snapshot();
    bool send(const nlohmann::json& event);
private:
    void run(int port, const std::string& token);
    std::atomic<bool> running_{false};
    std::thread thread_;
    std::mutex mutex_;
    nlohmann::json state_;
    std::deque<std::string> outgoing_;
};
}
