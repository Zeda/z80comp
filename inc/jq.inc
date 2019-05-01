#ifndef included_jq
#define included_jq

#macro jq(label)
  jp label
#endmacro

#macro jqz(label)
  jp z,label
#endmacro

#macro jqnz(label)
  jp nz,label
#endmacro

#macro jqc(label)
  jp c,label
#endmacro

#macro jqnc(label)
  jp nc,label
#endmacro



#endif
