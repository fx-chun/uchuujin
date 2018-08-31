#!/usr/bin/env python3

def alphanumTable():
    table = {}
    lines = open("alphanum.tbl", 'r', encoding="shift-jis").readlines()

    numcounter = 0x0092
    for x in range(0, 10):
        line = lines[x]
        num = int(line[0:4], 16)
        table[numcounter] = num 
        numcounter += 1

    capcounter = 0x009c
    for x in range(9, 35):
        line = lines[x]
        cap = int(line[0:4], 16)
        table[capcounter] = cap
        capcounter += 1

    lowcounter = 0x00b6
    for x in range(35, 61):
        line = lines[x]
        low = int(line[0:4], 16)
        table[lowcounter] = low 
        lowcounter += 1

    return table
