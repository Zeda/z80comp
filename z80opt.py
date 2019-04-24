def z80optimizer(src):
  #Takes in src as the source code
  #Returns optimized version
  #Only basic optimizations are performed
  s=[]
  for i in src.split("\n"):
    i=i.rstrip()
    if i!='':
      s+=[i]
  src=s+['']
  s=[]
  k=0
  while k<len(src):
    if src[k].startswith(" call ") and src[k+1]==" ret":
      s+=[" jp "+src[k][6:]]
      k+=2
    elif src[k].endswith("),hl") and src[k+1].startswith(" ld hl,(") and src[k][5:-3]==src[k+1][8:]:
      s+=[src[k]]
      k+=2
    elif src[k]==" ex de,hl" and src[k+1]==" ex de,hl":
      k+=2
    else:
      s+=[src[k]]
      k+=1
  src=""
  k=0
  while k<len(s):
    #if not (s[k].startswith(" jp ") and s[k+1]=='#include "'+s[k][4:]+'.z80"'):
    if not(s[k].startswith(" jp ") and s[k+1]=='#include "'+s[k][4:]+'.z80"'):
      src+=s[k]+"\n"
    k+=1
  return src
