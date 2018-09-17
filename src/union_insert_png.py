#!/usr/bin/env python3

import io
import sys
import math
import json
import textwrap
import gzip 
import time
from PIL import Image
import numpy as np
from os.path import basename, getsize, splitext

png = Image.open(sys.argv[1])
png_name = splitext(basename( sys.argv[1] ))[0]

chunk = png_name.split("_")[0]
index = int(png_name.split("_")[1]) - 1

chunk_f = open(chunk, 'rb')
chunk_raw = chunk_f.read()

meta_f = open(chunk + ".json")
meta = json.load(meta_f)

palette = meta[png_name]["palette_used"]

print("inserting %s into %s ..." % (png_name, chunk))

# read png into chunks

img = png.convert('RGBA')
arr = []

for yi in range(0, meta[png_name]["image_height"]):
    for xi in range(0, meta[png_name]["image_width"]):
        c = img.copy()
        c = c.crop((xi * 16, yi * 8, (xi+1) * 16, (yi+1) * 8))
        arr += c.getdata()

# map array into palette values

def colorDistance(c1, c2):
    r1, g1, b1, a1 = c1
    r2, g2, b2, a2 = c2

    # https://stackoverflow.com/questions/4754506/color-similarity-distance-in-rgba-color-space
    return (max((r1-r2)**2, (r1-r2 - a1+a2)**2) +
           max((g1-g2)**2, (g1-g2 - a1+a2)**2) +
           max((b1-b2)**2, (b1-b2 - a1+a2)**2))


def matchColorToPalette(color):
    smallestColorDistance = math.inf
    paletteValue = 0x0 

    for i in range(0, len(palette)):
        d = colorDistance(palette[i], color)

        if d < smallestColorDistance:
            paletteValue = i
            smallestColorDistance = d

    return paletteValue 

bin_raw = b''

for color in arr:
    p = matchColorToPalette(color)
    bin_raw += p.to_bytes(1, byteorder='big')

no_of_subfiles, first_subfile_id = meta["image_headers"][index]
subfile_size = math.floor(len(bin_raw)/no_of_subfiles)

subfiles = [bin_raw[i:i+subfile_size] for i in range(0, len(bin_raw), subfile_size)]

gzip_sizes = meta["gzip_sizes"][first_subfile_id:first_subfile_id+len(subfiles)]
gzip_offsets = meta["gzip_offsets"][first_subfile_id:first_subfile_id+len(subfiles)]
for i in range(0, len(subfiles)):
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='w', compresslevel=1, mtime=None) as fo:
        fo.write(bin_raw)
    compressed = out.getvalue()
    print(len(compressed))
    padded = compressed + b'\x00' * (gzip_sizes[i] - len(compressed))
    chunk_raw = chunk_raw[:gzip_offsets[i]] + padded + chunk_raw[gzip_offsets[i] + len(padded):]

# checksum
fp = io.BytesIO(chunk_raw)
fp.seek(0)
s = len(chunk_raw) 
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

chunk_raw = chunk_raw[:len(chunk_raw) - 16] + checksum

open(chunk, 'wb+').write(chunk_raw)
