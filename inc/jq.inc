#ifndef included_jq
#define included_jq

#macro jq(label)
#if label-$>125
  jp label
#elif $-label>128
  jp label
#else
  jr label
#endif
#endmacro

#macro jqz(label)
#if label-$>125
  jp z,label
#elif $-label>128
  jp z,label
#else
  jr z,label
#endif
#endmacro

#macro jqnz(label)
#if label-$>125
  jp nz,label
#elif $-label>128
  jp nz,label
#else
  jr nz,label
#endif
#endmacro

#macro jqc(label)
#if label-$>125
  jp c,label
#elif $-label>128
  jp c,label
#else
  jr c,label
#endif
#endmacro

#macro jqnc(label)
#if label-$>125
  jp nc,label
#elif $-label>128
  jp nc,label
#else
  jr nc,label
#endif
#endmacro



#endif
