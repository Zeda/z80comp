#ifndef included_gfx_inc
#define included_gfx_inc


#define LCDDelay()   in a,(16) \ rla \ jr c,$-3

#define spritetmp OP1
#define sprite_mask0 spritetmp+6
#define sprite_mask1 spritetmp+7
gbuf_ptr     = 80E0h


#endif
