#macro appheader(name,pages)
.org $4000
.db $80,$0F, 0,0,0,0
.db $80,$12, $01,$04    ;signing key ID
.db $80,+_-$+63,name    ;$80,$40+len(name),name
_:
.db $80,$81, pages      ;num pages
.db $80,$90             ;no splash
.db $03,$22,$09,$00     ;date stamp
.db $02,$00             ;date stamp signatur
.db $80,$70             ;final field

#endmacro
