#!/usr/bin/env python3

def kanjiTable():
    counter = 0x01eb

    table = {}
    
    for line in open("kanji.tbl", 'r', encoding="shift-jis").readlines():
        kanji = int(line[0:4], 16)
        table[counter] = kanji
        counter += 1

    return table

