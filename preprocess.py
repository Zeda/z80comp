#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys


def preprocess(src,):
    # First make a list of all of the labels
    labels = []
    for i in src:
        if i.endswith(":"):
            labels+=[i[0:-1]]

    # Intitialize a counter for temp labels
    temp = 0

    # Intitialize a program counter
    k = 0

    #Initialize the output
    out = []

    while k<len(src):
        if src[k].endswith("\tWhile("):
            #Replace the line with `lbl_1  Goto(\nlbl_0:`
            # Locate the matching `End`
            # replace the `End` with:
            #   lbl_1:
            #   (condition) lbl_0  GotoIf(
            cond=src[k][0:-6]

            # Generate temp labels
            while "lbl_"+str(temp) in labels:
                temp+=1
            lbl0="lbl_"+str(temp)
            labels+=[lbl0]
            temp+=1

            while "lbl_"+str(temp) in labels:
                temp+=1

            lbl1="lbl_"+str(temp)
            labels+=[lbl1]
            temp+=1

            out+=[lbl1+'\t'+"Goto(",lbl0+":"]

            #Find the matching End
            c = 1
            p = k
            while c > 0 and p<len(src):
                p+=1
                if src[p].endswith("\tWhile(") or src[p].endswith("\tIf("):
                    c+=1
                elif src[p]=="End":
                    c-=1

            if c!=0:
                raise Exception("Unmatched `End` for:\n\t"+src[k])
            src[p]=lbl1+":\n"+lbl0+"\t"+cond+"GotoIf("

        elif src[k].endswith("\tIf("):
            #  If there is a matching Else, then replace with
            #GotoIfNot(Else,condition)
            #  If there is a matching ElseIf, then replace with
            #GotoIfNot(ElseIf,condition) \ If
            #  If there is a matching End, then replace with
            #GotoIfNot(End,condition)

            cond=src[k][0:-3]

            # Generate temp label
            while "lbl_"+str(temp) in labels:
                temp+=1
            lbl0="lbl_"+str(temp)
            labels+=[lbl0]
            temp+=1

            #Find the matching End, Else, or ElseIf
            c = 1
            p = k
            while c > 0 and p<len(src):
                p+=1
                if src[p].endswith("\tWhile(") or src[p].endswith("\tIf("):
                    c+=1
                elif src[p]=="End":
                    c-=1
                elif src[p]=="Else" and c==1:
                    c-=1
                elif src[p].endswith("\tElseIf(") and c==1:
                    c-=1

            if c!=0:
                raise Exception("Unmatched `End` for:\n\t"+src[k])
            if src[p]=="End":
                src[p]=lbl0+":"
                out+=[lbl0+"\t"+cond+"GotoIfNot("]
            elif src[p]=="Else":
                print("'Else' not supported yet!")
            else:
                print("'ElseIf' not supported yet!")
        else:
            out+=[src[k]]
        k+=1
    s = ''
    for i in out:
        s+=i+"\n"
    return s


fi = ''
fo = ''
v  = False
if len(sys.argv)<3:
    print("{} source dest".format(sys.argv[0]))
    raise SystemExit

for i in sys.argv[1:]:
    if i=='-v':
      v=True

    elif fi == '':
        fi = i

    else:
        fo = i

if v:
    print("Preprocessing code from {}...".format(fi))

with open(fi, "r") as f:
    code = f.read()

with open(fo, 'w') as f:
    f.write(preprocess(code.split('\n')))

if v:
    print("Processing code to {}.".format(fi))
