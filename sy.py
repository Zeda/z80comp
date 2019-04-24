from math import sin
import sys,sqlite3,os
conn=sqlite3.connect("tokens.db")
c=conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS `tokens` (
  `name`  TEXT NOT NULL,
  `code`  TEXT NOT NULL,
  `bytecode`  TEXT NOT NULL,
  `sizescore`  INTEGER NOT NULL,
  `speedscore`  INTEGER NOT NULL,
  `type`  TEXT NOT NULL,
  `precedence`  INTEGER NOT NULL
)
""")
binops=c.execute("SELECT `name`,`precedence`,`code`,`bytecode` FROM tokens WHERE type='binop'").fetchall()+[['',0,'']]
varlist=[]
funclist=[]
labels=[]
org=0
for i in c.execute("SELECT `name`,`code`,`bytecode` FROM tokens WHERE type='func' ORDER BY `name` ASC").fetchall():
  funclist+=[list(i)]
def getbinopsinfo(s):
  #print(s)
  n=0
  m=len(binops)-1
  while (n<m) and s!=binops[n][0]:
    n+=1
  return binops[n]
def isvar(s):
  for i in varlist:
    if s==i[0]:
      return True
  return False
def isnum(s):
  for i in s:
    if ((i<"0") or (i>"9")) and (i!=".") and (i!='-'):
      return False
  return True
def optimizer(exp):
  n=len(exp)
  k=0
  while k<n:
    f=False
    if isnum(exp[k-1])==True:
      if exp[k]=="sin(":
        f=True
        s=str(sin(eval(exp[k-1])))
      if f==True:
        f=False
        if k==1:
          exp=[s]+exp[2:]
        else:
          exp=exp[0:k-1]+[s]+exp[k+1:]
        k-=1
        n-=1
      if isnum(exp[k-2])==True:
        if exp[k]=="+":
          f=True
          s=str(eval(exp[k-2])+eval(exp[k-1]))
        if exp[k]=="-":
          f=True
          s=str(eval(exp[k-2])-eval(exp[k-1]))
        if exp[k]=="*":
          f=True
          s=str(eval(exp[k-2])*eval(exp[k-1]))
        if exp[k]=="/":
          f=True
          s=str(eval(exp[k-2])/eval(exp[k-1]))
        if exp[k]=="^":
          f=True
          s=str(eval(exp[k-2])**eval(exp[k-1]))
        if f==True:
          if k==2:
            exp=[s]+exp[3:]
          else:
            exp=exp[0:k-2]+[s]+exp[k+1:]
          k-=2
          n-=2
    k+=1
  return exp
def shuntingyard(inp):
  global varlist
  size = len(inp)
  opstack=""
  out=""
  k=0
  inp+=" "
  while k<size:
    n=k
    while ("0"<=inp[k]<="9"):
      out+=inp[k]
      k+=1
    if inp[k]==".":
      out+=inp[k]
      k+=1
      while ("0"<inp[k]<="9"):
        out+=inp[k]
        k+=1
      if inp[k]==".":
        return "Err: Too Many Decimals."
    if n!=k:
      out+=","
    elif inp[k]==",":
      k+=1
    else:
#Check Variables
      while ("a"<=inp[k]<="z") or ("A"<=inp[k]<="Z") or ("0"<=inp[k]<="9") or inp[k]=="_":
        k+=1
      if n==k or inp[k]=="(":
        k=n
      else:
        if isvar(inp[n:k]):
          out+=inp[n:k]+","
        else:
          varlist+=[[inp[n:k],'','']]
          #return "Err: Var Not Found  :  "+inp[n:k]
          out+=inp[n:k]+","

    if inp[k]=="(":
      opstack="(,"+opstack
      k+=1
    if inp[k]==")":
      m=len(opstack)
      if m==0:
        return "Err: Unmatched ')'."
      n=0
      opstack+=" "
      while opstack[n]!="(" and n<m:
        n+=1
      if n==m:
        return "Err: Unmatched ')'."
      out+=opstack[0:n+2]
      opstack=opstack[n+2:-1]
      k+=1
    s=inp[k]
    if s=="\\":
      k+=1
      s+=inp[k]
    elif s=="!" and inp[k+1]=="=":
      k+=1
      s+="="
    n=getbinopsinfo(s)
    if n[0]!="":
      p=n[1]
      m=0
      j=len(opstack)
      opstack+=" "
      while (p<=getbinopsinfo(opstack[m])[1]) and m<j:
        m+=1
        if m<j:
          if opstack[m]==',':
            m+=1
        if m<j:
          if getbinopsinfo(opstack[m])[0]=='':
            j=m
      out+=opstack[0:m]
      opstack=n[0]+","+opstack[m:-1]
      k+=1
    if ("A"<inp[k]<="Z") or ("a"<inp[k]<="z"):
      n=k
      while (("A"<inp[k]<="Z") or ("a"<inp[k]<="z") or ("0"<inp[k]<="1") or (inp[k]=="_")) and k<size:
        k+=1
      if inp[k]=="(":
        k+=1
        opstack=inp[n:k]+","+opstack
      else:
        k=n
  out+=opstack
  out=out.replace(",(",'').strip(",")
  return out.split(",")
def compileline(exp):
  global varlist,org,labels
  exp=exp.strip()
  if exp=="":
    return []
  if exp.endswith(":"):
    return [exp]
  elif exp.startswith("var "):
    exp=exp[4:].split(" ")
    if len(exp)>2 or len(exp)==0:
      return "Err: Syntax"
    elif len(exp)==1:
      s="uint16"
      i=exp[0].split("=")
    else:
      i=exp[1].split("=")
      s=exp[0]
    if s=="int":
      s="int32"
    if s=="char":
      s="uint8"
    if s=="single":
      s="float"
    if s=="floatext" or s=="float" or s=="int8" or s=="int16" or s=="int32" or s=="int64" or s=="uint8" or s=="uint16" or s=="uint32" or s=="uint64":
      if len(i)==1:
        i+=["0"]
      if len(i)>2:
        return "Err: Syntax"
      varlist+=[[i[0],s,i[1]]]
      return ""
  return shuntingyard(exp)
def compile(code,opt=True):
  global varlist,org
  code=code.replace("\\","\\\\")
  code=code.replace("->","\\~")
  code=code.split("\n")
  out=[]
  k=0
  for i in code:
    k+=1
    s=compileline(i)
    if s[0:4]=="Err:":
      return "Line "+str(k)+"  "+s
    out+=s
  return out
#  return out
fi=''
fo=''
mode=''
asm=False
if len(sys.argv)==1:
  print("%s source [dest]" % sys.argv[0])
  raise SystemExit
for i in sys.argv[1:]:
  if i[0]=='-':
    pass
  else:
    if fi=='':
      fi=i
    else:
      fo=i
if fo=='':
  s=fi.split('.')
  fo=s[0]
  for i in s[1:-1]:
    fo+='.'+i
  fo+='.ir'
print("Generating intermediate code for %s" % fi)
f=open(fi,"r")
code=f.read()
f.close()
f=open(fo,'w')
f.close()

for i in code.split("\n"):
  s=compile(i)
  if s[0:4]=="Line":
    raise Exception("\n"+s+"\n")
  t=''
  for i in s:
    t+=i+'\t'
  f=open(fo,'a')
  f.write(t[0:-1])
  f.write("\n")
  f.close()
print("Output intermediate code to %s" % fo)
