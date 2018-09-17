#!/usr/bin/env python3

import re
import sys
import os
import zlib
import json

f_path = sys.argv[1]
f_name = os.path.basename(f_path)
f_size = os.path.getsize(f_path)
f = open(f_path, 'rb')
f_dump = f.read()

print("extracting %s ..." % f_name)

# Find gzip offsets
gzip_offsets = []

for match in re.finditer(b'\x1f\x8b\x08\x00', f_dump):
    gzip_offsets.append(match.start())

# Dump and decompress gzips
gzip_sizes = []
subfiles = []

for i in range(0, len(gzip_offsets)):
    offset = gzip_offsets[i]
    
    if i + 1 == len(gzip_offsets):
        next_offset = f_size
    else:
        next_offset = gzip_offsets[i + 1]
    
    gzip_size = next_offset - offset
    
    f.seek(offset)
    gzip = f.read(gzip_size)

    gzip_sizes.append(gzip_size)
    subfiles.append(zlib.decompress(gzip, 15+32))

print("subfiles: %d" % len(subfiles))

# Create image 
image_headers = []
images = []

supposed_subfiles = 0

for match in re.finditer(b'([\x01-\x10]\x00)\x00\x00(...\x00)*(\x1f\x8b\x08)', f_dump, re.DOTALL):
    if match.start() % 0x10 != 0:
        print("warning: image header not aligned")

    no_of_subfiles = int.from_bytes(match.groups()[0], byteorder='little')
    first_subfile_id = gzip_offsets.index(match.start(3))

    image = b''
    for i in range(first_subfile_id, first_subfile_id + no_of_subfiles):
        image += subfiles[i]

    images.append(image)
    image_headers.append((no_of_subfiles, first_subfile_id))
    supposed_subfiles += no_of_subfiles

if supposed_subfiles != len(subfiles):
    print("warning: headers lie, says there's only %s subfiles ..." % supposed_subfiles)

print("images: %d" % len(images))

# Parse palettes

# Dump .bin and .plt files 
f.seek(0)

image_number = 1
for image in images:
    binf = open( "%s_%d.bin" % (f_name, image_number), 'wb' )
    binf.write(image)

    pltf = open( "%s_%d.plt" % (f_name, image_number), 'wb' )
    pltf.write(f.read(0x100 * 4))

    image_number += 1


# Metadata

try:
    meta_f = open('%s.json' % f_name)
    meta = json.load(meta_f)
except FileNotFoundError:
    meta = {}

meta_f = open('%s.json' % f_name, 'w+')

meta["gzip_offsets"] = gzip_offsets
meta["gzip_sizes"] = gzip_sizes
meta["image_headers"] = image_headers

json.dump(meta, meta_f, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
