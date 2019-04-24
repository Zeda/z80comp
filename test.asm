#include "z80comp.inc"
#include "ti83plus.inc"
scrap           = 8000h
var_k           = scrap+0
var_x           = scrap+2
var_y           = scrap+4
var_s           = scrap+6
var_t           = scrap+8
.db $BB,$6D
.org $9D95
 ld hl,gbuf
 ld (gbuf_ptr),hl
 ld hl,617
 ld (var_k),hl
 ld hl,0
 ld (var_x),hl
 ld hl,0
 ld (var_y),hl
 ld hl,1
 ld (var_s),hl
 ld hl,1
 ld (var_t),hl
lbl0:
 ld de,0
 ld a,0
 ld hl,(var_y)
 ld c,l
 ld hl,(var_x)
 ld b,l
 call sprite8
 call UpdateLCD
 ld hl,(var_x)
 ld de,(var_s)
 add hl,de
 ld (var_x),hl
 ld hl,(var_y)
 ld de,(var_t)
 add hl,de
 ld (var_y),hl
 ld de,88
 ld hl,(var_x)
 or a
 sbc hl,de
 ld a,h
 or l
 jqnz(lbl1 )
 ld hl,(var_s)
 ld de,0
 ex de,hl
 or a
 sbc hl,de
 ld (var_s),hl
lbl1:
 ld hl,(var_x)
 ld a,h
 or l
 jqnz(lbl2 )
 ld hl,(var_s)
 ld de,0
 ex de,hl
 or a
 sbc hl,de
 ld (var_s),hl
lbl2:
 ld de,56
 ld hl,(var_y)
 or a
 sbc hl,de
 ld a,h
 or l
 jqnz(lbl3 )
 ld hl,(var_t)
 ld de,0
 ex de,hl
 or a
 sbc hl,de
 ld (var_t),hl
lbl3:
 ld hl,(var_y)
 ld a,h
 or l
 jqnz(lbl4 )
 ld hl,(var_t)
 ld de,0
 ex de,hl
 or a
 sbc hl,de
 ld (var_t),hl
lbl4:
 ld hl,(var_k)
 dec hl
 ld (var_k),hl
 ld a,h
 or l
 jqnz(lbl0 )
 ld hl,0
 ld a,h
 or l
 jqz(stop )
stop:
 ret
#include "sprite8.z80"
#include "UpdateLCD.z80"

