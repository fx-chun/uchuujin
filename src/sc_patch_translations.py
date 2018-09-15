#!/usr/bin/env python3

import json
import sys
import io
import math
import polib 
from os.path import basename
from sc_patch_table import patchTable

sc = open(sys.argv[1], 'rb')
sc_name = basename(sys.argv[1]) 
meta = json.load(open(sys.argv[2], 'r'), encoding='shift-jis')
po = polib.pofile(sys.argv[3]) 
patched_f = open(sc_name, 'wb')

patched = sc.read()
patched_len_orig = len(patched)

print("patching %s ..." % sc_name)

def asciiToNichi(asc):
    nichi = b''

    asc = asc.replace("...", chr(0xff))

    for c in list(asc):
        if c == '\n':
            if len(nichi) % 2 != 0:
                nichi += b'\x00'
        nichi += patchTable()[c]

    if len(nichi) % 2 != 0:
        nichi += b'\x00'

    return nichi

net = 0
for i in range(0, len(meta)):
    dialog = meta[i]

    speakerTranslation = ""
    textTranslation = ""


    for entry in po:
        if len(entry.msgstr) > 0: 
            if entry.msgid == dialog["speaker"]:
                speakerTranslation = entry.msgstr 
            
            if entry.msgid == dialog["text"]:
                textTranslation = entry.msgstr

    # Insert speaker
    if len(speakerTranslation) > 0:
        speaker = asciiToNichi(speakerTranslation)
        speaker_start = dialog["internal"]["speaker_offset"] + net
        speaker_end = dialog["internal"]["speaker_offset"] + dialog["internal"]["speaker_len"] + net

        patched = patched[:speaker_start] + speaker + patched[speaker_end:]
        net += len(speaker) - dialog["internal"]["speaker_len"]

    # Insert text
    if len(textTranslation) > 0:
        text = asciiToNichi(textTranslation + '\n')
        text_start = dialog["internal"]["text_offset"] + net
        text_end = dialog["internal"]["text_offset"] + dialog["internal"]["text_len"] + net

        patched = patched[:text_start] + text + patched[text_end:]
        net += len(text) - dialog["internal"]["text_len"]

diff = len(patched) - patched_len_orig
print("growth of file: %d" % diff)

if diff > 0:
    #pass
    patched = patched[:patched_len_orig] # + (b'\x00' * 1) 

    # closest_power = math.ceil( math.log(len(patched), 2) )
    # power = math.floor(math.pow(2, closest_power))

    # patched = patched + (b'\x00' * (power - len(patched)))
elif diff < 0:
    patched += b'\x00' * diff

# calculate checksum
fp = io.BytesIO(patched)
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
