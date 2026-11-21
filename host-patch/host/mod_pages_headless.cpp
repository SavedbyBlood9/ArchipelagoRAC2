// SPDX-License-Identifier: MIT
// Headless hosts have no rendered mod pages. Keep their game-facing API available.
#ifndef OPENRAC_FRONTEND
#include "openrac/game_host.h"
const openrac_mod_pages_host* openrac_game_mod_pages = nullptr;
int openrac_mod_pages_items(int) { return 0; }
int openrac_mod_pages_label(int, int, char* out, int size) {
    if(out && size>0)out[0]=0;
    return 0;
}
int openrac_mod_pages_after(int) { return 2; }
int openrac_mod_pages_view_of(openrac_mod_pages_view*) { return 0; }
#endif
