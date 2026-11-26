// SPDX-License-Identifier: MIT
#pragma once
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include "pal_boot_moves.hpp"
#include "ntsc2_boot_moves.hpp"

namespace rac2ap {
// The discs the mod knows: USA v1.01 (ntsc), Locked & Loaded PAL (pal) and USA v2.00 (ntsc2).
inline bool supported_disc(const std::string& version){
    return version=="ntsc"||version=="pal"||version=="ntsc2";
}

template<std::size_t N>
inline uint32_t move_address(const BootMove (&moves)[N],const char* disc,uint32_t primary){
    for(const auto& row:moves)if(primary>=row.first&&primary<=row.last)
        return static_cast<uint32_t>(static_cast<int64_t>(primary)+row.move);
    throw std::runtime_error(std::string("No verified ")+disc+" address mapping for "+std::to_string(primary));
}

// Runtime facts are expressed in USA v1.01 addresses. Translate the disc first,
// then ask the host to relocate that disc's global into the loaded overlay.
inline uint32_t disc_address(const std::string& version,uint32_t primary){
    if(version=="ntsc")return primary;
    if(version=="pal")return move_address(kPalBootMoves,"PAL",primary);
    if(version=="ntsc2")return move_address(kNtsc2BootMoves,"USA v2.00",primary);
    throw std::runtime_error("Unsupported ArchipelagoRAC2 disc version: "+version);
}
}
