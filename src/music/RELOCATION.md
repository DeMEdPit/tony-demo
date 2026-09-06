# TonyIntroA000_reloc.sid

A copy of `tonyintroe000_1.sid` (the intro tune, music by Sami Juntunen, MIT
licence in this folder) moved from $E000 to $A000 so that the Chamber can
carry it in the slot where it keeps the level tune. It was made after the
fact with `tools/sidreloc.py`, which runs the tune in a tag-tracking 6502
and changes only the bytes that serve as the high byte of an address inside
the tune (289 of 5,782 bytes, no conflicts). The two files were then played
side by side on the emulator for 24,000 frames (eight minutes) with
`tools/verify_reloc.py`, and every SID register write matched. No note,
instrument or timing differs from the original. The PSID header is the
original's, with the init and play addresses moved with the code.

    python3 tools/sidreloc.py src/music/tonyintroe000_1.sid src/music/TonyIntroA000_reloc.sid --to A000
    python3 tools/verify_reloc.py src/music/tonyintroe000_1.sid src/music/TonyIntroA000_reloc.sid
