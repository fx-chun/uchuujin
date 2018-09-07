#!/usr/bin/env python3

import string

def patchTable():
    table = {
        '\n': b'\xfe\xff',
        '?' : b'\x08\x00',
        '!' : b'\x09\x00',
        '.' : b'\x04\x00',
        ' ' : b'\x00\x00',
        '-' : b'\x1b\x00',
        ',' : b'\x03\x00',
        "'" : b'\x03\x00', # todo
        '#' : b'\x00\x00', # todo
        '(' : b'\x29\x00',
        ')' : b'\x2a\x00',
        '&' : b'\x54\x00'
    }

    counter = 0x009C
    for c in list(string.ascii_uppercase):
        table[c] = int.to_bytes(counter, length=2, byteorder='little')
        counter += 1

    counter = 0x00B6
    for c in list(string.ascii_lowercase):
        table[c] = int.to_bytes(counter, length=2, byteorder='little')
        counter += 1

    counter = 0x0092
    for n in list(string.digits):
        table[n] = int.to_bytes(counter, length=2, byteorder='little')
        counter += 1

    return table