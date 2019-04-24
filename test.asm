#include "jq.inc"
#include "ti83plus.inc"
scrap           = 8000h
var_k           = scrap+0
var_x           = scrap+2
var_y           = scrap+4
var_z           = scrap+6
.db $BB,$6D
.org $9D95
 ld hl,4
 ld (var_k),hl
 ld hl,0
 ld (var_x),hl
 ld hl,1
 ld (var_y),hl
lbl0:
 ld hl,(var_x)
 ld de,(var_y)
 add hl,de
 ld (var_z),hl
 ld hl,(var_x)
 inc hl
 ld (var_x),hl
 ld hl,(var_y)
 inc hl
 ld (var_y),hl
 ld hl,(var_z)
 add hl,hl
 add hl,hl
 ld de,(var_z)
 add hl,de
 add hl,hl
 call disp_uint16
 ld hl,(var_k)
 dec hl
 ld (var_k),hl
 ld a,h
 or l
 jqnz(lbl0 )
 ld hl,2
 ld (var_x),hl
#include "disp_uint16.z80"

