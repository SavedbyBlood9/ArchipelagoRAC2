// SPDX-License-Identifier: MIT
// Save-local replay and identity policy. Effects run on the game thread through callbacks.
#pragma once
#include <cstdint>
#include <functional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#include "json.hpp"

namespace rac2ap {
using json = nlohmann::json;
class Journal {
public:
    json identity;
    std::size_t cursor = 0;
    std::set<int> checks;
    bool goal = false;
    bool initialized = false;
    std::vector<int> applied;
    std::set<int> visited;
    std::set<double> deaths;

    void restore(const std::string& bytes) {
        *this = Journal{};
        if (bytes.empty()) return;
        auto data = json::parse(bytes);
        if (data.at("format") != 1) throw std::runtime_error("Unsupported APRac2 save format");
        identity = data.at("identity");
        cursor = data.at("cursor").get<std::size_t>();
        checks = data.at("checks").get<std::set<int>>();
        applied = data.at("applied").get<std::vector<int>>();
        visited = data.value("visited",std::set<int>{});
        deaths = data.value("deaths",std::set<double>{});
        goal = data.at("goal").get<bool>();
        initialized = true;
        if (cursor != applied.size()) throw std::runtime_error("Invalid APRac2 save item history");
    }
    std::string serialize() const {
        return json{{"format",1},{"identity",identity},{"cursor",cursor},
                    {"checks",checks},{"applied",applied},{"goal",goal},{"visited",visited},{"deaths",deaths}}.dump();
    }
    void bind(const json& current, bool fresh) {
        if (initialized) {
            if (identity != current) throw std::runtime_error("This save belongs to a different Archipelago seed/team/slot");
        } else {
            if (!fresh) throw std::runtime_error("An unbound existing save cannot be used for Archipelago; start a new game");
            identity = current;
            initialized = true;
        }
    }
    // Fail before any effects if the save and server disagree about their shared history.
    void validate_history(const std::vector<int>& items) const {
        if (!initialized || cursor > items.size()) throw std::runtime_error("Waiting for complete item history");
        for (std::size_t i=0;i<cursor;++i)
            if (applied[i] != items[i]) throw std::runtime_error("Saved item history belongs to a different seed");
    }
    void receive(const std::vector<int>& items, const std::function<void(int)>& give,
                 const std::function<void(const std::string&)>& checkpoint) {
        validate_history(items);
        while (cursor < items.size()) {
            // Integration must prevent saves inside give(), and make checkpoint nonthrowing.
            // This helper alone cannot make a game effect and a filesystem save atomic.
            give(items[cursor]);
            applied.push_back(items[cursor]); ++cursor;
            checkpoint(serialize());
        }
    }
    bool check(int id, const std::set<int>& active) {
        if (!initialized || !active.count(id)) throw std::runtime_error("Inactive APRac2 location");
        return checks.insert(id).second;
    }
};
}
