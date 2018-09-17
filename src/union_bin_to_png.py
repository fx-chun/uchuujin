#!/usr/bin/env python3

import sys
import zlib 
import math
import json
from os.path import basename, getsize, splitext
from PIL import Image

binf = open( sys.argv[1], 'rb' )
binf_name = splitext(basename( sys.argv[1] ))[0]
binf_size = getsize( sys.argv[1] )
binf_raw = binf.read()

if len(sys.argv) >= 4:
    pltf = open(sys.argv[3], 'rb')
else:
    pltf = open( "%s.plt" % binf_name, 'rb' )

print("converting %s ..." % binf_name)
print("using palette %s" % pltf)

palette = []

while True:
    bs = pltf.read(4)

    if len(bs) < 4:
        break

    color = ( bs[0], bs[1], bs[2], bs[3] )
    palette.append(color)

print(len(palette))

# magic 
#palette[0xfe] = ( 255, 255, 255, 0 )

pixels = [ palette[int(x)] for x in binf_raw]

chunks = []
chunk_width = 16
chunk_height = 8
chunk_size = chunk_width * chunk_height
chunks_total = math.ceil(len(pixels) / chunk_size)

if len(pixels) % chunk_size != 0:
    print("warning: chunks possibly wrong size ...")

for chunk_i in range(0, chunks_total):
    chunk_start = chunk_i * chunk_size
    chunk_end = chunk_start + chunk_size 
    
    chunk = Image.new("RGBA", (16, 8))
    chunk.putdata(pixels[chunk_start:chunk_end])

    chunks.append(chunk)

image_width = 0

if len( sys.argv ) >= 3:
    image_width = int(sys.argv[2])
else:
    image_width = 32

#    while True:
#        r, g, b, a = chunks[image_width].getpixel((0, 0))
#    
#        if r == 0xff and g == 0xff and a == 0x0:
#            image_width += 2
#            break
#    
#        image_width += 1

image_height = math.floor(chunks_total / image_width)

if chunks_total % image_width != 0:
    print("warning: left over chunks")

print("chunks total:\t%d" % len(chunks))
print("image width (chunks):\t%d" % image_width)
print("image height (chunks):\t%d" % image_height)

image = Image.new("RGBA", (chunk_width * image_width, chunk_height * image_height))
chunk_i = 0
for yi in range(0, image_height):
    for xi in range(0, image_width):
        image.paste(chunks[chunk_i], (xi * chunk_width, yi * chunk_height))
        chunk_i += 1

image.save( "%s.png" % binf_name, "PNG" )

# Metadata
base = binf_name.split('_')[0]

try:
    meta_f = open('%s.json' % base)
    meta = json.load(meta_f)
except FileNotFoundError:
    meta = {}

meta[binf_name] = {}
meta_f = open('%s.json' % base, 'w+')

meta[binf_name]["palette_used"] = palette 
meta[binf_name]["image_width"] = image_width
meta[binf_name]["image_height"] = image_height

json.dump(meta, meta_f, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
