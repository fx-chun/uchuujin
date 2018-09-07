#!/usr/bin/env python3

import json
import sys
import io
import math
from os.path import basename
from sc_patch_table import patchTable

sc = open(sys.argv[1], 'rb')
sc_name = basename(sys.argv[1]) 
trans = json.load(open(sys.argv[2], 'r'), encoding='shift-jis')
patched_f = open(sc_name, 'wb')

patched = sc.read()
patched_len_orig = len(patched)

def asciiToNichi(str):
    nichi = b''

    for c in list(str):
        nichi += patchTable()[c]
    
    return nichi

net = 0
for i in range(0, len(trans)):
    dialog = trans[i]

    # Insert speaker
    if len(dialog["speaker_translation"]) > 0:
        speaker = asciiToNichi(dialog["speaker_translation"])
        speaker_start = dialog["internal"]["speaker_offset"] + net
        speaker_end = dialog["internal"]["speaker_offset"] + dialog["internal"]["speaker_len"] + net

        patched = patched[:speaker_start] + speaker + patched[speaker_end:]
        net += len(speaker) - dialog["internal"]["speaker_len"]

    # Insert text
    if len(dialog["text_translation"]) > 0:
        text = asciiToNichi(dialog["text_translation"] + '\n')
        text_start = dialog["internal"]["text_offset"] + net
        text_end = dialog["internal"]["text_offset"] + dialog["internal"]["text_len"] + net

        patched = patched[:text_start] + text + patched[text_end:]
        net += len(text) - dialog["internal"]["text_len"]

diff = len(patched) - patched_len_orig

print(diff)

if diff > 0:
    closest_power = math.ceil( math.log(len(patched), 2) )
    power = math.floor(math.pow(2, closest_power))

    patched = patched + (b'\x00' * (power - len(patched)))
elif diff < 0:
    patched += b'\x00' * diff

# calculate checksum
fp = io.BytesIO(patched)
#fp = sc
fp.seek(0)
s = len(patched) 
p1 = 0x11111111
p2 = 0x11111111
p3 = 0x11111111
p4 = 0x11111111
m  = 0xffffffff
s -= 16
while s > 0: 
    a1 = int.from_bytes(fp.read(4), byteorder='little')
    a2 = int.from_bytes(fp.read(4), byteorder='little')
    a3 = int.from_bytes(fp.read(4), byteorder='little') 
    a4 = int.from_bytes(fp.read(4), byteorder='little') 

    p1 += a1
    p1 = p1 & m

    if p1 < a1:
        p2 += 1 + a2
    else:
        p2 += 0 + a2
    p2 = p2 & m

    p3 += a3
    p3 = p3 & m

    if p3 < a3:
        p4 += 1 + a4
    else:
        p4 += 0 + a4

    p4 = p4 & m 

    s -= 16

print("%x %x %x %x" % (p1, p2, p3, p4))

p1 = int.to_bytes(p1, length=4, byteorder='little')
p2 = int.to_bytes(p2, length=4, byteorder='little')
p3 = int.to_bytes(p3, length=4, byteorder='little')
p4 = int.to_bytes(p4, length=4, byteorder='little')

checksum = p1 + p2 + p3 + p4

patched = patched[:len(patched) - 16] + checksum

patched_f.write(patched)
