// SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <stdexcept>
#include <string>
#include "pal_boot_moves.hpp"

namespace rac2ap {
// Runtime facts are expressed in USA v1.01 addresses. Translate the disc first,
// then ask the host to relocate that disc's global into the loaded overlay.
inline uint32_t disc_address(const std::string& version,uint32_t primary){
    if(version=="ntsc")return primary;
    if(version!="pal")throw std::runtime_error("Unsupported ArchipelagoRAC2 disc version: "+version);
    for(const auto& row:kPalBootMoves)if(primary>=row.first&&primary<=row.last)
        return static_cast<uint32_t>(static_cast<int64_t>(primary)+row.move);
    throw std::runtime_error("No verified PAL address mapping for "+std::to_string(primary));
}
}
