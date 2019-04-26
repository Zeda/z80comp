def z80optimizer(src):
    """Takes in src as the source code
    Returns optimized version
    Only basic optimizations are performed"""
    # Remove empty linesIn
    linesIn = [x.rstrip() for x in src.split("\n") if x.rstrip()]
    linesOut = []
    i = 0
    while i < len(linesIn):
        line = linesIn[i]
        nextLine = linesIn[i + 1] if i + 1 < len(linesIn) else ''
        if line.startswith(" call ") and nextLine == " ret":
            linesOut += [" jp " + line[6:]]

        elif line.endswith("),hl") and \
                nextLine.startswith(" ld hl,(") and \
                line[5:-3] == nextLine[8:]:
            linesOut += [line]

        elif line != " ex de,hl" or nextLine != " ex de,hl":
            linesOut += [line]
            i += 1
            continue

        i += 2

    ret = ""
    for i in range(0, len(linesOut)):
        line = linesOut[i]
        if not line.startswith(" jp ") or \
                linesOut[i + 1] != '#include "{}.z80"'.format(line[4:]):
            ret += "{}\n".format(line)

    return ret
