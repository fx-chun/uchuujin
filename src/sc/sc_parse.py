#!/usr/bin/env python3

# Parses sc unpacked script files from sc.cpk
# Usage: sc_parse.py <sc file>

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
logs_dir = "logs/"


# Class to define and reset vars
class parsingVars():
    # Default vars
    def __init__(self):
        self.rawread = []
        self.magic1 = False
        self.dialog = -1
        self.speaker = []
        self.magic2 = False
        self.text = []
        self.magic3 = False
        self.speaker_offset = -1
        self.text_offset = -1

    def reset(self):
        self.__init__()


v = parsingVars()

# Testing class
print(vars(v))
v.magic1 = True
print(vars(v))
# print(v.magic1)
v.reset()
print(vars(v))


# Main var for jis lookups

# Update jisTable for punctuation
# Eventually create .tbl file like the others?
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
# Read in other tables and add onto the existing dict
jisTable.update(kanjiTable())
jisTable.update(alphanumTable())


# Convert Nichijou text characters to Shift-JIS
def nichiToJIS(bs, logFile):
    jis = ""
    warnings = 0

    for b in bs:
        printable = True

        if b in jisTable:            # JIS Table lookup
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
            logFile.write(f"Unknown kanji {hex(b)} at {bs}\n")
            printable = False
            warnings += 1
            # logFile.write(f'Warnings: {warnings}\n')
        elif 0xf000 <= b <= 0xffff:  # control characters
            print("NOTE: control character %s" % hex(b))
            logFile.write(f"Control character {hex(b)} at {bs}\n")
            printable = False
            warnings += 1
            # logFile.write(f'Warnings: {warnings}\n')
        else:                       # unknown
            print(f"WARNING: unknown character {hex(b)}")
            logFile.write(f"Unknown character {hex(b)} at {bs}\n")
            printable = False
            warnings += 1
            # logFile.write(f'Warnings: {warnings}\n')

        if printable:
            b = b.to_bytes(2, 'big')
            jis += b.decode("shift-jis")

    return jis, warnings


# ---------------------------- Convert sc to json ----------------------- #
def sc_parse(scFilePath):
    # Set up logging
    logFilePath = logs_dir + os.path.split(scFilePath)[-1] + ".txt"
    print(logFilePath)
    logFile = open(logFilePath, "w+")

    # Open sc file
    scfile = open(scFilePath, 'rb')
    scfile_name = basename(scFilePath)

    # Create json var
    jsonFilePath = json_dir + scfile_name + ".json"
    # encoding can also be "Shift-JIS", same for pofile
    jsonfile = open(jsonFilePath, 'w', encoding='UTF-8')
    print(f"Dumping script {scfile_name} ...")

    lastdialog = -1

    v.reset()

    output = []

    while True:
        # bs = First 2 bytes of sc file
        bs = scfile.read(2)

        # If sc file is less than 2 bytes, break loop
        if len(bs) < 2:
            break

        # Put each byte into separate entries in rawread list var
        v.rawread.append(bs[0])
        v.rawread.append(bs[1])

        # Takes bs bytes and converts to int
        lbs = int.from_bytes(bs, byteorder='little')

        # If magic1 var is not True, ???
        if not v.magic1:
            if bs[0] == 0xf0 and bs[1] == 0xff:
                v.magic1 = True
            else:
                result = {
                    "type": "raw_pair",
                    # Convert bs bytes to their 2-digit hex representation,
                    # then to ascii
                    "data": binascii.hexlify(bs).decode('ascii')
                }

                # output.append(result)
                v.reset()

        #
        elif v.magic1 and not v.magic2:
            if v.dialog < 0:
                if lbs > lastdialog:
                    v.dialog = lbs
                    lastdialog = lbs
                else:
                    v.reset()
            elif bs[0] == 0xff and bs[1] == 0xff and len(v.speaker) > 0:
                v.magic2 = True
            elif bs[0] == 0xff and bs[1] == 0xff:
                result = {
                    "type": "raw_chunk",
                    "data":
                        binascii.hexlify(bytearray(v.rawread)).decode('ascii')
                }

                # output.append(result)
                v.reset()
            else:
                if v.speaker_offset < 0:
                    v.speaker_offset = scfile.tell() - 0x2
                v.speaker.append(lbs)
        elif v.magic1 and v.magic2 and not v.magic3:
            if bs[0] == 0xfb and bs[1] == 0xff:
                v.magic3 = True
            elif bs[0] == 0xfd and bs[1] == 0xff:
                v.magic3 = True
            elif bs[0] == 0x98 and bs[1] == 0xff:
                v.magic3 = True
            elif bs[0] == 0xfe and bs[1] == 0xff:
                v.text.append(ord('\n'))
            else:
                if v.text_offset < 0:
                    v.text_offset = scfile.tell() - 0x2
                v.text.append(lbs)
        elif v.magic3:
            speakerJIS, warnings_speaker = nichiToJIS(v.speaker, logFile)
            # print("[ %s ]" % speakerJIS)

            textJIS, warnings_text = nichiToJIS(v.text, logFile)
            # print(textJIS)

            textraw = []
            for b16 in v.text:
                msb, lsb = struct.pack('<H', b16)
                textraw.append(msb)
                textraw.append(lsb)

            speakerraw = []
            for b16 in v.speaker:
                msb, lsb = struct.pack('<H', b16)
                speakerraw.append(msb)
                speakerraw.append(lsb)

            result = {
                "type": "dialog",
                "id": v.dialog,
                "speaker": speakerJIS,
                "text": textJIS,
                "internal": {
                    "warnings": warnings_speaker + warnings_text,
                    "speaker_offset": v.speaker_offset,
                    "speaker_len": len(speakerraw),
                    "text_offset": v.text_offset,
                    "text_len": len(textraw)
                }
            }

            output.append(result)
            v.reset()

    json.dump(output, jsonfile, ensure_ascii=False,
              sort_keys=True, indent=4, separators=(',', ': '))
    print(f"{jsonFilePath} dumped!")

    # ---------------------------- Generate .po file ------------------------ #
    print("Generating .po file...")

    poFilePath = po_dir + "%s.po" % scfile_name
    pofile = open(poFilePath, 'w', encoding='UTF-8')

    for v.dialog in output:
        if len(v.dialog["speaker"]) > 0:
            pofile.write("\n")
            pofile.write("#: sc/%s:%d \n" % (scfile_name, v.dialog["id"]))
            pofile.write("#  speaker \n")
            pofile.write("#  warnings: %d \n"
                         % v.dialog["internal"]["warnings"])

            pofile.write("msgid \"%s\"\n" % v.dialog["speaker"])
            pofile.write("msgstr \"\"\n")

        if len(v.dialog["text"]) > 0:
            pofile.write("\n")
            pofile.write("#: sc/%s:%d \n"
                         % (scfile_name, v.dialog["id"]))
            pofile.write("#  text \n")
            pofile.write("#  warnings: %d \n"
                         % v.dialog["internal"]["warnings"])

            pofile.write("msgid \"%s\"\n" % v.dialog["text"])
            pofile.write("msgstr \"\"\n")

    print(f"{poFilePath} generated!")

    print("Done!\n")


# -------------------------- Command line interface ------------------------- #
if sys.argv[1] == "all":
    all_dir = sys.argv[2]
    for filename in os.listdir(all_dir):
        sc_parse(all_dir + filename)
else:
    sc_parse(sys.argv[1])
