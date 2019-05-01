#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import sqlite3
import caribou

from z80comp import z80optimizer
from z80comp import isnum

#  These two help decide worthy tradeoffs in optimization
# SPEED_MOD=0.0 would mean that only size matters in optimization
# SIZE_MOD =0.0 would mean that only speed matters in optimization
# SPEED_MOD=1.0, SIZE_MOD=6.0 would mean we are willingly to gain 1 byte to save 6cc.

SPEED_MOD = 1.0
SIZE_MOD = 6.0

PATH_SORT_MODE_DEPTH = 0
PATH_SORT_MODE_SCORE = 1
PATH_SORT_MODE = PATH_SORT_MODE_SCORE

MAX_PATHS = 100  # Set this to zero for no pruning


class Node:

    def __init__(self, val='', desc=[]):
        self.value = val
        self.desc = desc
        self.parents = []
        self.children = []

    def addparent(self, node):
        node.addchild(self)
        return self

    def addchild(self, node):
        self.children = [node] + self.children
        if self not in node.parents:
            node.parents += [self]

        return self

    def child(self, n):
        if n >= len(self.children):
            return Node()

        return self.children[n]

    def parent(self, n):
        return self.parent[n]

    def copy(self):
        n = Node(self.value, self.desc)
        for i in self.children[::-1]:
            n.addchild(i.copy())

        return n

    def __str__(self):
        s = str(self.value) + '['
        for i in self.children:
            s += str(i) + ','

        return (s.rstrip(',') + ']').replace('[]', '')

    def __eq__(self, n):
        if self.desc == n.desc and self.value == n.value:
            f = True
            for i in range(self.desc[0]):
                f &= self.child(i) == n.child(i)

            return f
        else:

            return False


class Code:

    def __init__(
        self,
        c='',
        o='',
        d=[],
        state='',
    ):
        self.out = o
        self.destroys = d
        self.code = c
        self.state = state

    def copy(self):
        return Code(self.code, self.out, self.destroys[0:], self.state)


class Path:

    def __init__(
        self,
        i=0,
        size=0,
        speed=0,
        code=[],
        req=[],
        vars=[],
    ):
        self.index = i
        self.size = size
        self.speed = speed
        self.code = code
        self.vars = vars
        self.requires = req

    def copy(self):
        return Path(
            self.index,
            self.size,
            self.speed,
            [x.copy() for x in self.code],
            self.requires[0:],
            self.vars[0:],
        )

    def __eq__(self, p):
        if PATH_SORT_MODE == PATH_SORT_MODE_SCORE:
            return self.size * SIZE_MOD + self.speed * SPEED_MOD \
                == p.size * SIZE_MOD + p.speed * SPEED_MOD
        else:

            return self.index == p.index

    def __ne__(self, p):
        if PATH_SORT_MODE == PATH_SORT_MODE_SCORE:
            return self.size * SIZE_MOD + self.speed * SPEED_MOD \
                != p.size * SIZE_MOD + p.speed * SPEED_MOD
        else:

            return self.index != p.index

    def __ge__(self, p):
        if PATH_SORT_MODE == PATH_SORT_MODE_SCORE:
            return self.size * SIZE_MOD + self.speed * SPEED_MOD \
                >= p.size * SIZE_MOD + p.speed * SPEED_MOD
        else:

            return self.index >= p.index

    def __gt__(self, p):
        if PATH_SORT_MODE == PATH_SORT_MODE_SCORE:
            return self.size * SIZE_MOD + self.speed * SPEED_MOD \
                > p.size * SIZE_MOD + p.speed * SPEED_MOD
        else:

            return self.index > p.index

    def __le__(self, p):
        if PATH_SORT_MODE == PATH_SORT_MODE_SCORE:
            return self.size * SIZE_MOD + self.speed * SPEED_MOD \
                <= p.size * SIZE_MOD + p.speed * SPEED_MOD
        else:

            return self.index <= p.index

    def __lt__(self, p):
        if PATH_SORT_MODE == PATH_SORT_MODE_SCORE:
            return self.size * SIZE_MOD + self.speed * SPEED_MOD \
                < p.size * SIZE_MOD + p.speed * SPEED_MOD
        else:

            return self.index < p.index


def getglue(o, i):
    if o == i:
        return ['', 0, 0, '']
    reg8 = [
        'B',
        'C',
        'D',
        'E',
        'H',
        'L',
        '(hl)',
        'A',
        'IXH',
        'IXL',
    ]

    if i == 'H' or i == 'L':
        s = 'HL'
    elif i == 'D' or i == 'E':
        s = 'DE'
    elif i == 'B' or i == 'C':
        s = 'BC'
    elif i == 'IXH' or i == 'IXL':
        s = 'IX'
    elif i == 'A':
        s = 'AF'

    if o.endswith('HL') and i.endswith('HL'):
        return ['', 0, 0, ['']]

    elif o.endswith('HL') and i.endswith('DE'):
        return ['ex de,hl', 2, 8, ['DE', 'HL']]
        return ['ld d,h \\ ld e,l', 2, 8, ['DE']]

    elif o.endswith('HL') and i.endswith('BC'):
        return ['ld b,h \\ ld c,l', 2, 8, ['BC']]

    elif o.endswith('HL') and i.endswith('IX'):
        return ['push hl \ pop ix', 3, 25, ['IX']]

    elif o.endswith('DE') and i.endswith('HL'):
        return ['ex de,hl', 2, 8, ['DE', 'HL']]
        return ['ld h,d \\ ld l,e', 2, 8, ['HL']]

    elif o.endswith('DE') and i.endswith('DE'):
        return ['', 0, 0, ['']]

    elif o.endswith('DE') and i.endswith('BC'):
        return ['ld b,d \\ ld c,e', 2, 8, ['BC']]

    elif o.endswith('DE') and i.endswith('IX'):
        return ['push de \ pop ix', 3, 25, ['IX']]

    elif o.endswith('BC') and i.endswith('HL'):
        return ['ld h,b \\ ld l,c', 2, 8, ['HL']]

    elif o.endswith('BC') and i.endswith('DE'):
        return ['ld d,b \\ ld e,c', 2, 8, ['BC']]

    elif o.endswith('BC') and i.endswith('BC'):
        return ['', 0, 0, ['']]

    elif o.endswith('BC') and i.endswith('IX'):
        return ['push bc \ pop ix', 3, 25, ['IX']]

    elif o.endswith('IX') and i.endswith('HL'):
        return ['push ix \ pop hl', 3, 25, ['HL']]

    elif o.endswith('IX') and i.endswith('DE'):
        return ['push ix \ pop de', 3, 25, ['DE']]

    elif o.endswith('IX') and i.endswith('BC'):
        return ['push ix \ pop bc', 3, 25, ['BC']]

    elif o.endswith('IX') and i.endswith('IX'):
        return ['', 0, 0, ['']]

    elif o in reg8 and i.endswith('HL'):
        return ['ld l,' + o.lower() + " \ ld h,0", 3, 11, ['HL']]

    elif o in reg8 and i.endswith('DE'):
        return ['ld e,' + o.lower() + " \ ld d,0", 3, 11, ['DE']]

    elif o in reg8 and i.endswith('BC'):
        return ['ld c,' + o.lower() + " \ ld b,0", 3, 11, ['BC']]

    elif o in reg8 and i.endswith('IX'):
        return ['ld ixl,' + o.lower() + " \ ld ixh,0", 3, 11, ['IX']]

    elif o.endswith('HL') and i in reg8:
        return ['ld ' + i.lower() + ',l', 1, 4, [s]]

    elif o.endswith('DE') and i in reg8:
        return ['ld ' + i.lower() + ',e', 1, 4, [s]]

    elif o.endswith('BC') and i in reg8:
        return ['ld ' + i.lower() + ',c', 1, 4, [s]]

    elif o.endswith('IX') and i in reg8:
        return ['ld ' + i.lower() + ',ixl', 2, 8, [s]]

    elif o in reg8 and i in reg8:
        return ['ld ' + i.lower() + ',' + o.lower(), 1, 4, [s]]

    else:
        raise Exception("""Can't glue "%s ==> %s" """ % (o, i))


def compile(src, c):
    global PATH_SORT_MODE

    # Each path is:
    #   Index into the source
    #   Size score
    #   Speed score
    #   Code path
    # Each element of the code path is [outputs, destroys, code]

    paths = [Path()]
    count = 0
    while paths[0].index < len(src):
        pth = paths[0].copy()
        paths = paths[1:]
        s = src[pth.index]
        p = c.execute("""
            SELECT
                code,
                size,
                speed,
                input,
                output,
                destroys,
                requires,
                state
            FROM z80
            WHERE ir=?
        """, (s, )).fetchall()
        if p == []:
            if s.endswith('\\~'):
                p0 = c.execute("""
                    SELECT
                        code,
                        size,
                        speed,
                        input,
                        output,
                        destroys,
                        requires,
                        state
                    FROM z80
                    WHERE ir=?
                """, ('\\sto', )).fetchall()
                s = 'var_' + s[0:-3]
                if s not in pth.vars:
                    pth.vars += [s]
            elif s.endswith('GotoIf('):
                if s.startswith('0 = '):
                    p0 = c.execute("""
                        SELECT
                            code,
                            size,
                            speed,
                            input,
                            output,
                            destroys,
                            requires,
                            state
                        FROM z80 WHERE ir=?
                    """, ('0 = GotoIf(', )).fetchall()
                    s = s[4:-7]
                elif s.startswith('0 != '):
                    p0 = c.execute("""
                    SELECT
                        code,
                        size,
                        speed,
                        input,
                        output,
                        destroys,
                        requires,
                        state
                    FROM z80
                    WHERE ir=?
                """, ('0 != GotoIf(', )).fetchall()
                    s = s[5:-7]
                else:
                    p0 = c.execute("""
                        SELECT
                            code,
                            size,
                            speed,
                            input,
                            output,
                            destroys,
                            requires,
                            state
                        FROM z80
                        WHERE ir=?
                    """, ('GotoIf(', )).fetchall()
                    s = s[0:-7]
            elif s.endswith('GotoIfNot('):
                if s.startswith('0 = '):
                    p0 = c.execute("""
                        SELECT
                            code,
                            size,
                            speed,
                            input,
                            output,
                            destroys,
                            requires,
                            state
                        FROM z80 WHERE ir=?
                    """, ('0 = GotoIfNot(', )).fetchall()
                    s = s[4:-10]
                elif s.startswith('0 != '):
                    p0 = c.execute("""
                    SELECT
                        code,
                        size,
                        speed,
                        input,
                        output,
                        destroys,
                        requires,
                        state
                    FROM z80
                    WHERE ir=?
                """, ('0 != GotoIfNot(', )).fetchall()
                    s = s[5:-10]
                else:
                    p0 = c.execute("""
                        SELECT
                            code,
                            size,
                            speed,
                            input,
                            output,
                            destroys,
                            requires,
                            state
                        FROM z80
                        WHERE ir=?
                    """, ('GotoIfNot(', )).fetchall()
                    s = s[0:-10]
            elif s.endswith('Goto('):
                p0 = c.execute("""
                    SELECT
                        code,
                        size,
                        speed,
                        input,
                        output,
                        destroys,
                        requires,
                        state
                    FROM z80 WHERE ir=?
                """, ('Goto(', )).fetchall()
                s = s[0:-5]
            elif isnum(src[pth.index]):
                p0 = c.execute("""
                SELECT
                    code,
                    size,
                    speed,
                    input,
                    output,
                    destroys,
                    requires,
                    state
                FROM z80
                WHERE (ir=? AND output LIKE ?)
            """, ('\\constant', "%%int16%%",)).fetchall()
            else:
                p0 = c.execute("""
                    SELECT
                        code,
                        size,
                        speed,
                        input,
                        output,
                        destroys,
                        requires,
                        state
                    FROM z80
                    WHERE ir=?
                """, ('\\var', )).fetchall()
                s = 'var_' + s
                if s not in pth.vars:
                    pth.vars += [s]
            for i in p0:
                i = list(i)
                i[0] = i[0].replace('**', s)
                p += [i]
        if p == []:
            raise Exception('Token Not Found: %s' % s)
        for i in p:
            j = pth.copy()

            # If i does not take input, need to append a new Code object
            # Otherwise, need to pop off code objects to match inputs

            if i[3] == '':

                # Just add the code object

                j.code += [Code(i[0], i[4], i[5].split(','), i[7])]

                # Push the new code path onto the paths list

                if i[6] not in j.requires:
                    j.requires += [i[6]]
                j.size += i[1]
                j.speed += i[2]
                j.index += 1
                paths += [j.copy()]
            else:

                # if the operation is commutative, then we should try to
                # rearange the inputs!
                # For binary ops, this doubles the space we are trying,
                # but may improve results

                codes = [j.copy()]
                if iscommutative(s):
                    j.code[-2:] = j.code[-2:][::-1]
                    codes += [j.copy()]
                for j in codes:
                    cod = Code()
                    cod.out = []
                    cod.destroys = []
                    if cod.destroys != []:
                        print(cod.destroys)
                        raw_input('Halp!')
                    for ins in i[3].split(','):
                        inp = ins.strip().split('=')
                        op = j.code[-1].copy()
                        j.code = j.code[:-1]

                        # Add the glue code so that op's output is correct

                        g = getglue(op.out.split('=')[0], inp[0])
                        op.code += " \ " + g[0]
                        j.size += g[1]
                        j.speed += g[2]
                        for d in g[3]:
                            if d not in op.destroys:
                                op.destroys += [d]
                        op.out = inp[0]

                        # Make sure that op doesn't destroy the outputs of cod

                        for codo in cod.out:
                            if codo in op.destroys:

                                # If cod.out is HL or DE and op.destroys doesn't
                                # contain the other, we can use `ex de,hl`
                                # Otherwise, just push \ pop

                                if codo.endswith('HL') and 'DE' \
                                        not in op.destroys:
                                    op.destroys += ['DE']
                                    op.code = "ex de,hl \ " + op.code + " \ ex de,hl"
                                    j.size += 2
                                    j.speed += 8
                                elif codo.endswith('DE') and 'HL' \
                                        not in op.destroys:
                                    op.destroys += ['HL']
                                    op.code = "ex de,hl \ " + op.code + " \ ex de,hl"
                                    j.size += 2
                                    j.speed += 8
                                else:

                                    # Here we push \ pop
                                    # However, if cod has gluecode to pass
                                    # registers, we might be able to get rid of it!

                                    if codo.endswith('ld b,h \\ ld c,l') or \
                                            codo.endswith("ld c,l \ ld b,h"):
                                        cod.code = cod.code[-15:]
                                        op.code = "push hl \ " + op.code + \
                                            " \ pop bc"
                                        j.speed += 13
                                    elif codo.endswith('ld b,d \\ ld c,e') or \
                                            codo.endswith("ld c,e \ ld b,d"):
                                        cod.code = cod.code[-15:]
                                        op.code = "push de \ " + op.code + \
                                            " \ pop bc"
                                        j.speed += 13
                                    elif codo.endswith('ld d,h \\ ld e,l') or \
                                            codo.endswith("ld e,l \ ld d,h"):
                                        cod.code = cod.code[-15:]
                                        op.code = "push hl \ " + op.code + \
                                            " \ pop de"
                                        j.speed += 13
                                    elif codo.endswith('ld h,b \\ ld l,c') or \
                                            codo.endswith("ld l,c \ ld h,b"):
                                        cod.code = cod.code[-15:]
                                        op.code = "push bc \ " + op.code + \
                                            " \ pop hl"
                                        j.speed += 13
                                    elif codo.endswith('ld d,b \\ ld e,c') or \
                                            codo.endswith("ld e,c \ ld d,b"):
                                        cod.code = cod.code[-15:]
                                        op.code = "push bc \ " + op.code + \
                                            " \ pop de"
                                        j.speed += 13
                                    elif codo.endswith('ld h,d \\ ld l,e') or \
                                            codo.endswith("ld l,e \ ld h,d"):
                                        cod.code = cod.code[-15:]
                                        op.code = "push de \ " + op.code + \
                                            " \ pop hl"
                                        j.speed += 13
                                    else:
                                        op.code = 'push ' + codo.lower() + \
                                            " \ " + op.code + " \ pop " + \
                                            codo.lower()
                                        j.size += 2
                                        j.speed += 13

                        # Now we need to append op to cod

                        for d in op.destroys:
                            if d not in cod.destroys:
                                cod.destroys += [d]
                        cod.out += [op.out]
                        cod.code += " \ " + op.code

                    # Append the operator's code to cod

                    cod.code += " \ " + i[0]
                    cod.code = cod.code.replace('\\  \\', '\\')
                    cod.out = i[4]
                    for d in i[5].split(','):
                        if d not in cod.destroys:
                            cod.destroys += [d]
                    p0 = c.execute("""
                        SELECT
                            code,
                            size,
                            speed,
                            input,
                            output,
                            destroys,
                            requires,
                            state
                        FROM z80
                        WHERE ir=?
                    """, ('\\var', )).fetchall()

                    # Push a copy of cod into j's code
                    j.code += [cod.copy()]

                    # Push the new code path onto the paths list
                    if i[6] not in j.requires:
                        j.requires += [i[6]]
                    j.size += i[1]
                    j.speed += i[2]
                    j.index += 1
                    paths += [j.copy()]

            if MAX_PATHS != 0:
                PATH_SORT_MODE = PATH_SORT_MODE_DEPTH
                paths = sorted(paths, reverse=True)[0:MAX_PATHS]

            PATH_SORT_MODE = PATH_SORT_MODE_SCORE
            paths = sorted(paths)
            count += 1
    if v:
        print('%d paths searched' % count)

    p = paths[0]
    for i in p.code[1:]:
        p.code[0].code += i.code

    return p


caribou.upgrade('./z80comp.db', 'migrations')
conn = sqlite3.connect('z80comp.db')
c = conn.cursor()
p = c.execute('SELECT name,numargs,precedence,type FROM tokens'
              ).fetchall()
conn.close()
tokens = []
for i in p:
    i = list(i)
    if i[3] == 'func':
        i[0] += '('

    tokens += [list(i)]


def numargs(s):
    k = 0
    while k < len(tokens):
        if s == tokens[k][0]:
            return tokens[k][1]
        k += 1
    return 0


def iscommutative(s):
    return s in [
        '+',
        '*',
        'min(',
        'max(',
        '=',
        '!=',
    ]


def astgen(l):
    k = numargs(l[-1])
    n = Node(l[-1], desc=[k])
    l = l[0: - 1]
    if len(l) == 0 or k == 0:
        return [n, l]

    while k > 0:
        c = astgen(l)
        n.addchild(c[0].copy())
        l = c[1]
        k -= 1

    return [n, l]


def astoptimize(n):

    # Optimize each node

    for i in range(n.desc[0]):
        n.children[i] = astoptimize(n.child(i))

    # For commutative operations, put the input with fewest children on the
    # right, or constant inputs

    for i in range(n.desc[0] - 1):
        if iscommutative(n.value):
            if n.child(i).desc[0] < n.child(i + 1).desc[0] \
                    or isnum(n.child(i).value):
                a = n.child(i)
                n.children[i] = n.child(i + 1)
                n.children[i + 1] = a

    # Perform some replacements. ex, 2*x ==> x<<1

    if n.value == '+' and n.child(0).value == '*' and \
            n.child(1).value == '*':
        if n.child(0).child(0) == n.child(1).child(0):

            # then we have x*y+x*z ==> x*(y+z)

            x = n.child(0).child(0).copy()
            y = n.child(0).child(1).copy()
            z = n.child(1).child(1).copy()
            n = Node('*', [2])
            n.addchild(Node('+', [2]))
            n.children[0].addchild(y)
            n.children[0].addchild(z)
            n.addchild(x)

        elif n.child(0).child(1) == n.child(1).child(1):
            # then we have x*y+x*z ==> x*(y+z)
            x = n.child(0).child(1).copy()
            y = n.child(0).child(0).copy()
            z = n.child(1).child(0).copy()
            n = Node('*', [2])
            n.addchild(Node('+', [2]))
            n.children[0].addchild(y)
            n.children[0].addchild(z)
            n.addchild(x)

        return n
    elif n.value == '++' and '<<' in n.child(0).value:
        n.children[0].value += ' ++'
        return n.child(0)
    elif n.value == '*' and isnum(n.child(1).value):
        if isnum(n.child(0).value):
            return Node(str(int(n.child(0)) * int(n.child(1))), [0])

        p = c.execute("""
            SELECT ir
            FROM z80
            WHERE ir=?
        """, (n.child(1).value + ' *', )).fetchone()
        p = None  # TODO - WHAT IS THIS HERE FOR!
        if p is not None:
            n.value = n.child(1).value + ' *'
            n.children = [n.children[0]]
            n.desc = [1]
            return n

        else:
            t = int(n.child(1).value)
            if t == 0:
                return Node('0', [0])

            elif t == 1:
                return n.child(0)
            elif t - 1 & t == 0:
                k = 1
                i = 2
                while i != t:
                    i += i
                    k += 1
                n.value = '<<'
                n.children[1].value = str(k)
                return n

            else:
                return n

    elif n.value == '<<' and isnum(n.child(1).value):
        if int(n.child(1).value) == 0:
            return n.child(0)
        p = c.execute("""
            SELECT ir
            FROM z80
            WHERE ir=?
        """, (n.child(1).value + ' <<', )).fetchone()
        if p is not None:
            n.value = n.child(1).value + ' <<'
            n.children = [n.children[0]]
            n.desc = [1]

        return n

    elif n.value == '-' and n.child(1).value == '0':
        return n.child(0)

    elif n.value == '-' and n.child(0).value == '0':
        n.value='\\-'
        n.desc=[0]
        n.children=[n.child(1)]
        return n

    elif n.value == '-' and n.child(1).value == '1':
        n.children = [n.children[0]]
        n.value = '--'
        n.desc = [1]
        return n

    elif n.value == '+' and n.child(1).value == '0':
        return n.child(0)

    elif n.value == '+' and n.child(1).value == '1':
        n.children = [n.children[0]]
        n.value = '++'
        n.desc = [1]
        return n

    elif n.value == '+' and isnum(n.child(1).value):
        if isnum(n.child(0).value):
            return Node(str(int(n.child(0).value) + int(n.child(1).value)), [0])

        p = c.execute("""
            SELECT ir
            FROM z80
            WHERE ir=?
        """, (n.child(1).value + ' +', )).fetchone()
        if p is not None:
            n.value = n.child(1).value + ' +'
            n.children = [n.children[0]]
            n.desc = [1]

        return n

    elif n.value == '\\~':
        n.value = n.child(1).value + ' ' + n.value
        n.desc = [1]
        n.children = [n.children[0]]
        return n

    elif n.value == 'GotoIf(':
        n.value = n.child(0).value + ' ' + n.value
        n.desc = [1]
        n.children = [n.children[1]]
        return n

    elif n.value == 'GotoIfNot(':
        n.value = n.child(0).value + ' ' + n.value
        n.desc = [1]
        n.children = [n.children[1]]
        return n

    elif n.value == 'Goto(':
        n.value = n.child(0).value + ' ' + n.value
        n.desc = [0]
        n.children = []
        return n

    elif n.value == '=' and n.child(1).value == '0':
        n.value = '0 ='
        n.children = [n.child(0)]
        n.desc = [1]
        return n

    elif n.value == '=' and n.child(0).value == '0':
        n.value = '0 ='
        n.children = [n.child(1)]
        n.desc = [1]
        return n

    elif n.value.endswith('GotoIf(') and n.child(0).value == '0 =':
        n.value = n.child(0).value + ' ' + n.value
        n.desc = [1]
        n.children = [n.child(0).child(0)]
        return n

    elif n.value.endswith('GotoIfNot(') and n.child(0).value == '0 =':
        n.value = n.child(0).value + ' ' + n.value
        n.desc = [1]
        n.children = [n.child(0).child(0)]
        return n

    elif n.value == '!=' and n.child(1).value == '0':
        n.value = '0 !='
        n.children = [n.child(0)]
        n.desc = [1]
        return n

    elif n.value == '!=' and n.child(0).value == '0':
        n.value = '0 !='
        n.children = [n.child(1)]
        n.desc = [1]
        return n

    elif n.value.endswith('GotoIf(') and n.child(0).value == '0 !=':
        n.value = n.child(0).value + ' ' + n.value
        n.desc = [1]
        n.children = [n.child(0).child(0)]
        return n

    elif n.value.endswith('GotoIfNot(') and n.child(0).value == '0 !=':
        n.value = n.child(0).value + ' ' + n.value
        n.desc = [1]
        n.children = [n.child(0).child(0)]
        return n

    else:
        return n


def astoptimize2(n):

    # Optimize each node

    for i in range(n.desc[0]):
        n.children[i] = astoptimize2(n.child(i))

    # For commutative operations, put the input with fewest children on the
    # right, or constant inputs

    for i in range(n.desc[0] - 1):
        if iscommutative(n.value):
            if n.child(i).desc[0] < n.child(i + 1).desc[0] \
                    or isnum(n.child(i).value):
                a = n.child(i)
                n.children[i] = n.child(i + 1)
                n.children[i + 1] = a

    # Perform some replacements. ex, 2*x ==> x<<1
    if n.value == '*' and isnum(n.child(1).value):
        if isnum(n.child(0).value):
            return Node(str(int(n.child(0)) * int(n.child(1))), [0])

        p = c.execute("""
            SELECT ir
            FROM z80
            WHERE ir=?
        """, (n.child(1).value + ' *', )).fetchone()
        p = None  # TODO - WHAT THE HECK?
        if p is not None:
            n.value = n.child(1).value + ' *'
            n.children = [n.children[0]]
            n.desc = [1]
            return n

        else:
            t = int(n.child(1).value)
            if t == 0:
                return Node('0', [0])

            elif t == 1:
                return n.child(0)

            elif t - 1 & t == 0:
                k = 1
                i = 2
                while i != t:
                    i += i
                    k += 1

                n.value = '<<'
                n.children[1].value = str(k)
                return n

            elif (t - 1 & t) - 1 & t - 1 & t == 0:
                # multiply by 2^m(2^l+1)
                k = t & t - 1
                t -= k
                m = 0
                i = 1
                while i != t:
                    m += 1
                    i += i

                l = -m
                i = 1
                while i != k:
                    l += 1
                    i += i

                # So I have *(x,2^m(2^l+1)) == > (x+x<<l)<<m
                n0 = Node('<<', [2])
                n0.children = [n.child(0).copy(), Node(str(l), [0])]
                n1 = Node('+', [2])
                n1.children = [n.child(0).copy(), n0]
                n2 = Node('<<', [2])
                n2.children = [n1, Node(str(m), [0])]
                return n2

            else:
                return n
    else:
        return n


def asttorpn(n):
    l = [n.value]
    for i in n.children[::-1]:
        l = asttorpn(i) + l

    return l


def movreg(o, i):
    o = o.strip()
    i = i.strip()
    if o == i:
        return ''
    if o.endswith(i):
        return ''
    if o.endswith('HL') and i.endswith('DE') or o.endswith('DE') \
            and i.endswith('HL'):
        return " \ ex de,hl"

    elif o.endswith('HL') and i.endswith('BC'):
        return " \ ld b,h \ ld c,l"

    elif o.endswith('DE') and i.endswith('BC'):
        return " \ ld b,d \ ld c,e"

    elif o.endswith('BC') and i.endswith('DE'):
        return " \ ld d,b \ ld e,c"

    elif o.endswith('BC') and i.endswith('HL'):
        return " \ ld h,b \ ld l,c"

    else:
        s = "Can't move regs!\n           " + o + ' ==> ' + i
        raise Exception(s)


def astcompile(n, outp=''):
    # We need to compile this node so that it has the right output

    global c
    # Get all of the options for this tree
    p = c.execute("""
        SELECT
            code,
            input,
            output,
            destroys
        FROM z80
        WHERE ir=?
        AND output LIKE ?
        ORDER BY size * size * 36 + speed * speed ASC
    """, (n.value, '%' + outp + '=%')).fetchall()
    if p == []:
        p = c.execute("""
            SELECT
                code,
                input,
                output,
                destroys
            FROM z80
            WHERE ir=?
            ORDER BY size * size * 36 + speed * speed ASC
        """, (n.value, )).fetchall()
        if p == []:
            if isnum(n.value):
                p = c.execute("""
                    SELECT
                        code,
                        input,
                        output,
                        destroys
                    FROM z80
                    WHERE ir=?
                    AND output LIKE ?
                    ORDER BY size * size * 36 + speed * speed ASC
                """, ('constant', '%' + outp + '=%')).fetchall()
            else:
                p = c.execute("""
                    SELECT
                        code,
                        input,
                        output,
                        destroys
                    FROM z80
                    WHERE ir = ?
                    AND output LIKE ?
                    ORDER BY size * size * 36 + speed * speed ASC
                """, ('var', '%' + outp + '=%')).fetchall()

            if p == []:
                raise Exception(n)

    p = p[0]
    n.destroys = []
    k = 0
    ins = p[1].split(',')
    while k < len(n.children):
        n.children[k] = astcompile(
            n.child(k),
            (ins[k].strip().split('=')[0])[-2:]
        )
        for j in n.children[k].destroys:
            if j not in n.destroys:
                n.destroys += [j]

        k += 1
    if n.desc[0] == 0:
        n.code = p[0].replace('**', n.value)
        n.outp = [p[2]]
        if p[2] not in n.destroys:
            s = p[2].split('=')[0].split(':')
            n.destroys += s

        return n

    for i in p[3]:
        if i in n.destroys:
            n.destroys += [i]

    # We have the code, now we need to match inputs!
    code = p[0]
    inp = p[1].split(',')
    n.outp = p[2].split(',')
    if inp == []:
        return n

    n.code = n.child(0).code
    if len(inp) == 1:
        o = n.child(0).outp[0].split('=')
        i = inp[0].split('=')
        if o[0].endswith(i[0]):
            n.code += " \ " + code
            return n

        n.code += movreg(o[0], i[0]) + " \ " + code
        return n

    elif len(inp) == 2:
        o1 = n.child(0).outp[0].split('=')
        i1 = inp[0].split('=')
        o2 = n.child(1).outp[0].split('=')
        i2 = inp[1].split('=')
        if (o1[0])[-2:] in n.child(1).destroys or o1[0] == o2[0]:
            f = (o1[0])[-2:] == 'HL' and 'DE' \
                not in n.child(1).destroys or (o1[0])[-2:] == 'DE' \
                and 'HL' not in n.child(1).destroys
            if f:
                n.code += " \ ex de,hl"

            else:
                n.code += " \ push " + (o1[0])[-2:].lower()

            n.code += " \ " + n.child(1).code
            m = movreg(o2[0], i2[0])
            if ('ld b,' in m or 'ld c,' in m) and 'BC' \
                    not in n.destroys:
                n.destroys += ['BC']

            if ('ld d,' in m or 'ld e,' in m) and 'DE' \
                    not in n.destroys:
                n.destroys += ['DE']

            if ('ld h,' in m or 'ld l,' in m) and 'HL' \
                    not in n.destroys:
                n.destroys += ['HL']

            if ('ld ixh,' in m or 'ld ixl,' in m) and 'IX' \
                    not in n.destroys:
                n.destroys += ['IX']

            # Now move the outputs to the right inputs

            n.code += m

            # Now pop and go

            if f:
                n.code += " \ ex de,hl"

            else:
                n.code += " \ pop " + i1[0].lower()

            n.code += " \ " + code
            return n

        else:
            n.code += " \ " + n.child(1).code

            # Now move the outputs to the right inputs

            m = movreg(o2[0], i2[0])
            if ('ld b,' in m or 'ld c,' in m) and 'BC' \
                    not in n.destroys:
                n.destroys += ['BC']

            if ('ld d,' in m or 'ld e,' in m) and 'DE' \
                    not in n.destroys:
                n.destroys += ['DE']

            if ('ld h,' in m or 'ld l,' in m) and 'HL' \
                    not in n.destroys:
                n.destroys += ['HL']

            if ('ld ixh,' in m or 'ld ixl,' in m) and 'IX' \
                    not in n.destroys:
                n.destroys += ['IX']

            n.code += m
            m = movreg(o1[0], i1[0])
            if ('ld b,' in m or 'ld c,' in m) and 'BC' \
                    not in n.destroys:
                n.destroys += ['BC']

            if ('ld d,' in m or 'ld e,' in m) and 'DE' \
                    not in n.destroys:
                n.destroys += ['DE']

            if ('ld h,' in m or 'ld l,' in m) and 'HL' \
                    not in n.destroys:
                n.destroys += ['HL']

            if ('ld ixh,' in m or 'ld ixl,' in m) and 'IX' \
                    not in n.destroys:
                n.destroys += ['IX']

            n.code += m + " \ " + code
            return n

    else:
        raise Exception('Not handling more than two arguments!')


fi = ''
fo = ''
mode = ''
TI8X = False
SCRAP = '8000h'
SCRAP_SIZE = 256
includes = ['z80comp']
v=False
if len(sys.argv) == 1:
    print(""")
    {} [flags] source [dest]
        -TI8X will include headers for the TI-83+/84+ calculators
        -TI8X-<<shell>> will include the headers for the designated shell
        -SCRAP=xxxx will set the location of scrap
        -SCRAP_SIZE=x will set the size of scrap
        -v    for verbose mode
    """.format(sys.argv[0]))
    raise SystemExit()

for i in sys.argv[1:]:
    if i[0] == '-':
        if i.startswith('-TI8X'):
            TI8X = True
            if i[0:5] != '' and i[5:] not in includes:
                includes += [i[5:]]

            if 'ti83plus' not in includes:
                includes += ['ti83plus']

        elif i.startswith('-SCRAP='):
            SCRAP = i[7:]

        elif i.startswith('-SCRAP_SIZE='):
            SCRAP_SIZE = int(i[12:])

        elif i.startswith('-MAX_PATHS='):
            MAX_PATHS = int(i[11:])
        elif i.startswith('-MAX_PATHS='):
            MAX_PATHS = int(i[11:])
        elif i=="-v":
          v=True

    elif fi == '':
        fi = i
    else:
        fo = i

if fo == '':
    s = fi.split('.')
    fo = s[0]
    for i in s[1:-1]:
        fo += '.' + i

    fo += '.asm'

if v:
    print('Generating Z80 code from {}'.format(fi))

with open(fi, 'r') as f:
    code = f.read().strip()

# Load the description database
conn = sqlite3.connect('z80comp.db')
c = conn.cursor()
src = ''
vars = []
incs = []
for i in code.split('\n'):
    # Split the input
    if i.endswith(':'):
        src += '\n' + i

    else:
        s = i.strip().split('\t')
        if s != ['']:
            ast = astgen(s)[0]
            s = ''
            while s != asttorpn(ast):
                s = asttorpn(ast)
                ast = astoptimize(ast)
                ast = astoptimize2(ast)

            # ast=astcompile(ast)

            s = asttorpn(ast)
            p = compile(s, c)
            for i in p.vars:
                if i not in vars:
                    vars += [i]

            for i in p.requires:
                if i not in incs:
                    incs += [i]

            src += '\n ' + p.code[0].code

src += " \ ret"
for i in incs:
    src += '\n' + i

s = src
s = s.replace(' \\', '\n')
while '  ' in s:
    s = s.replace('  ', ' ')

s = z80optimizer(s)

# Generate the headers

t = ''
for i in includes:
    if i != '':
        t += '#include "' + i.lower() + '.inc"\n'
        if i.lower() not in ['ti83plus', 'z80comp']:
            t += '#include "' + i.lower() + '_z80comp.inc"\n'

# Create equates for the var locations
if 2 * len(vars) > SCRAP_SIZE:
    raise Exception(
        'SCRAP not big enough! Need {} bytes.'.format(2 * len(vars))
    )

if len(vars) != 0:
    t += 'scrap           = ' + SCRAP + '\n'
    loc = 0
    for i in vars:
        i += ' ' * (16 - len(i))
        i += '= scrap+' + str(loc)
        loc += 2
        t += i + '\n'

if TI8X:
    t += '.db $BB,$6D\n.org $9D95\n'

# Add the header
s = t + s

# Close the database
conn.close()

with open(fo, 'w') as f:
    f.write(s)

if v:
    print('Output Z80 code to {}'.format(fo))
