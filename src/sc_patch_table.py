#!/usr/bin/env python3

import string

def patchTable():
    table = {
        '\n': b'\xfe\xff',
        '?' : b'\x08',
        '!' : b'\x09',
        '.' : b'\x04',
        ' ' : b'\x00',
        '-' : b'\x1b',
        ',' : b'\x03',
        "'" : b'\x03', # todo
        '#' : b'\x00', # todo
        '(' : b'\x29',
        ')' : b'\x2a',
        '&' : b'\x54',
        
        chr(0xff) : b'\x23'
    }

    counter = 0x009C
    for c in list(string.ascii_uppercase):
        table[c] = int.to_bytes(counter, length=1, byteorder='little')
        counter += 1

    counter = 0x00B6
    for c in list(string.ascii_lowercase):
        table[c] = int.to_bytes(counter, length=1, byteorder='little')
        counter += 1

    counter = 0x0092
    for n in list(string.digits):
        table[n] = int.to_bytes(counter, length=1, byteorder='little')
        counter += 1

    return table

def findPatch(i):
    if (i in patchTable().keys()):
        return patchTable()[i];
    else:
        print("warn: could not find patch for '%s'\n" % (i));
        return patchTable()['?'];
