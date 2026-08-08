"""
Compile translation/000.po into the binary MO file translation/000.

This is a stand-in for GNU `msgfmt` so you do not have to install gettext.
It handles the metadata block plus simple (non-plural, non-fuzzy) entries,
which is all a display-only language pack needs.

Usage:
    python make_meta.py
"""

import re
import struct
from pathlib import Path

PO_PATH = Path("translation/000.po")
MO_PATH = Path("translation/000")


def unquote(line):
    # Strip the surrounding double quotes and unescape the usual sequences.
    text = line.strip()
    match = re.match(r'^"(.*)"$', text, re.DOTALL)
    if not match:
        return ""
    body = match.group(1)
    return body.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")


def parse_po(path):
    entries = {}
    msgid = None
    msgstr = None
    mode = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            # A new msgid closes the previous entry.
            if msgid is not None and msgstr is not None:
                entries[msgid] = msgstr
            msgid = unquote(line[len("msgid "):])
            msgstr = None
            mode = "id"
        elif line.startswith("msgstr "):
            msgstr = unquote(line[len("msgstr "):])
            mode = "str"
        elif line.startswith('"'):
            # A bare quoted line continues whichever field came before it.
            if mode == "id":
                msgid += unquote(line)
            elif mode == "str":
                msgstr += unquote(line)
    if msgid is not None and msgstr is not None:
        entries[msgid] = msgstr
    return entries


def write_mo(entries, path):
    # Entries must be sorted by msgid for the binary search the MO format assumes.
    items = sorted(entries.items(), key=lambda kv: kv[0].encode("utf-8"))
    keys = [k.encode("utf-8") for k, _ in items]
    values = [v.encode("utf-8") for _, v in items]

    count = len(items)
    key_table_offset = 28
    value_table_offset = key_table_offset + count * 8
    data_offset = value_table_offset + count * 8

    key_entries = b""
    value_entries = b""
    payload = b""
    offset = data_offset

    for key in keys:
        key_entries += struct.pack("<II", len(key), offset)
        payload += key + b"\x00"
        offset += len(key) + 1
    for value in values:
        value_entries += struct.pack("<II", len(value), offset)
        payload += value + b"\x00"
        offset += len(value) + 1

    header = struct.pack(
        "<IIIIIII",
        0x950412DE,
        0,
        count,
        key_table_offset,
        value_table_offset,
        0,
        0,
    )
    path.write_bytes(header + key_entries + value_entries + payload)


entries = parse_po(PO_PATH)
write_mo(entries, MO_PATH)
print(f"Wrote {MO_PATH} ({MO_PATH.stat().st_size} bytes, {len(entries)} entries)")
