#!/usr/bin/env python3

# Parses sc unpacked script files from sc.cpk
# Usage: sc_parse.py <sc file>

# TODO
# BUG: Control characters and warnings flood terminal on certain scripts
# BUG: Warning unknown characters: 0x18, 0x8e

# Import libraries
import os
import struct
import binascii
import json
import sys
from os.path import basename


# Import modules
from sc_generate_kanji_table import kanjiTable
from sc_generate_alphanum_table import alphanumTable

# Directory vars
json_dir = "scripts/"
po_dir = json_dir + "en_US/"
sc_dumps_dir = "sc_dumps/"


def sc_parse(scFile):
    # ---------------------------- Convert sc to json ----------------------- #
    # Open sc file
    scfile = open(scFile, 'rb')
    scfile_name = basename(scFile)

    # Create json var
    # encoding can also be "Shift-JIS", same for pofile
    jsonfile = open(json_dir + "%s.json" % scfile_name, 'w', encoding='UTF-8')
    print("Dumping script %s ..." % scfile_name)

    rawread = []
    magic1 = False
    dialog = -1
    speaker = []
    magic2 = False
    text = []
    magic3 = False
    speaker_offset = -1
    text_offset = -1

    lastdialog = -1

    def resetVars():
        # global rawread
        # global magic1
        # global dialog
        # global speaker
        # global magic2
        # global text
        # global magic3
        # global speaker_offset
        # global text_offset

        rawread = []
        magic1 = False
        dialog = -1
        speaker = []
        magic2 = False
        text = []
        magic3 = False
        speaker_offset = -1
        text_offset = -1

    resetVars()

    output = []

    jisTable = {
        0x0000: 0x8140,  # nul
        0x0001: 0x8141,  #
        0x0002: 0x8142,  # period
        0x0003: 0x8143,  # comma
        0x0004: 0x8144,  # period
        0x0005: 0x8145,  #
        0x0006: 0x8146,  # colon
        0x0007: 0x8147,  # semicolon
        0x0008: 0x8148,  # question mark
        0x0009: 0x8149,  # exclamation point
        0x0010: 0x8150,  #
        0x0019: 0x8159,  #
        0x001b: 0x815c,  # emdash
        0x001e: 0x815e,  # slash
        0x0020: 0x8160,  # tilde
        0x0023: 0x8163,  # ellipses
        0x0029: 0x8169,  # left paren
        0x002a: 0x816a,  # right paren
        0x002f: 0x816f,  # left bracket
        0x0030: 0x8170,  # right bracket
        0x0054: 0x8195,  # ampersand
    }

    jisTable.update(kanjiTable())
    jisTable.update(alphanumTable())

    def nichiToJIS(bs):
        jis = ""
        warnings = 0

        for b in bs:
            printable = True

            if b in jisTable:           # JIS Table lookup
                b = jisTable[b]
            elif b == ord('\n'):
                jis += "\\n"
                printable = False
            elif 0x00d0 <= b <= 0x0122:  # hiragana
                b += 0x81cf
            elif 0x0123 <= b <= 0x0161:  # katakana
                b += 0x821d
            elif 0x0162 <= b <= 0x0178:  # katakana (1 byte JIS offset)
                b += 0x821e
            elif 0x01eb <= b <= 0x1abc:  # uncaught kanji
                print("WARNING: unknown kanji %s" % hex(b))
                printable = False
                warnings += 1
            elif 0xf000 <= b <= 0xffff:  # control characters
                print("NOTE: control character %s" % hex(b))
                printable = False
                warnings += 1
            else:                       # unknown
                print("WARNING: unknown character %s" % hex(b))
                printable = False
                warnings += 1

            if printable:
                b = b.to_bytes(2, 'big')
                jis += b.decode("shift-jis")

        return jis, warnings

    while True:
        bs = scfile.read(2)

        if len(bs) < 2:
            break

        rawread.append(bs[0])
        rawread.append(bs[1])

        lbs = int.from_bytes(bs, byteorder='little')

        if not magic1:
            if bs[0] == 0xf0 and bs[1] == 0xff:
                magic1 = True
            else:
                result = {
                    "type": "raw_pair",
                    "data": binascii.hexlify(bs).decode('ascii')
                }

                # output.append(result)
                resetVars()
        elif magic1 and not magic2:
            if dialog < 0:
                if lbs > lastdialog:
                    dialog = lbs
                    lastdialog = lbs
                else:
                    resetVars()
            elif bs[0] == 0xff and bs[1] == 0xff and len(speaker) > 0:
                magic2 = True
            elif bs[0] == 0xff and bs[1] == 0xff:
                result = {
                    "type": "raw_chunk",
                    "data":
                        binascii.hexlify(bytearray(rawread)).decode('ascii')
                }

                # output.append(result)
                resetVars()
            else:
                if speaker_offset < 0:
                    speaker_offset = scfile.tell() - 0x2
                speaker.append(lbs)
        elif magic1 and magic2 and not magic3:
            if bs[0] == 0xfb and bs[1] == 0xff:
                magic3 = True
            elif bs[0] == 0xfd and bs[1] == 0xff:
                magic3 = True
            elif bs[0] == 0x98 and bs[1] == 0xff:
                magic3 = True
            elif bs[0] == 0xfe and bs[1] == 0xff:
                text.append(ord('\n'))
            else:
                if text_offset < 0:
                    text_offset = scfile.tell() - 0x2
                text.append(lbs)
        elif magic3:
            speakerJIS, warnings_speaker = nichiToJIS(speaker)
            # print("[ %s ]" % speakerJIS)

            textJIS, warnings_text = nichiToJIS(text)
            # print(textJIS)

            textraw = []
            for b16 in text:
                msb, lsb = struct.pack('<H', b16)
                textraw.append(msb)
                textraw.append(lsb)

            speakerraw = []
            for b16 in speaker:
                msb, lsb = struct.pack('<H', b16)
                speakerraw.append(msb)
                speakerraw.append(lsb)

            result = {
                "type": "dialog",
                "id": dialog,
                "speaker": speakerJIS,
                "text": textJIS,
                "internal": {
                    "warnings": warnings_speaker + warnings_text,
                    "speaker_offset": speaker_offset,
                    "speaker_len": len(speakerraw),
                    "text_offset": text_offset,
                    "text_len": len(textraw)
                }
            }

            output.append(result)
            resetVars()

    json.dump(output, jsonfile, ensure_ascii=False,
              sort_keys=True, indent=4, separators=(',', ': '))

    # ---------------------------- Generate .po file ------------------------ #
    print("Generating .po file...")

    pofile = open(po_dir + "%s.po" % scfile_name, 'w', encoding='UTF-8')

    for dialog in output:
        if len(dialog["speaker"]) > 0:
            pofile.write("\n")
            pofile.write("#: sc/%s:%d \n" % (scfile_name, dialog["id"]))
            pofile.write("#  speaker \n")
            pofile.write("#  warnings: %d \n" % dialog["internal"]["warnings"])

            pofile.write("msgid \"%s\"\n" % dialog["speaker"])
            pofile.write("msgstr \"\"\n")

        if len(dialog["text"]) > 0:
            pofile.write("\n")
            pofile.write("#: sc/%s:%d \n" % (scfile_name, dialog["id"]))
            pofile.write("#  text \n")
            pofile.write("#  warnings: %d \n" % dialog["internal"]["warnings"])

            pofile.write("msgid \"%s\"\n" % dialog["text"])
            pofile.write("msgstr \"\"\n")

    print("Done!\n")


# -------------------------- Command line interface ------------------------- #
if sys.argv[1] == "all":
    all_dir = sys.argv[2]
    for filename in os.listdir(all_dir):
        sc_parse(all_dir + filename)
else:
    sc_parse(sys.argv[1])
