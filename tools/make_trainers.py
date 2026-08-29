#!/usr/bin/env python3
"""Generate the two trainer builds of the full game from tony.asm.

  src/kickass/tony-trained.asm         -> tony-trained.prg
      No menu at all: boots straight into the game like the original,
      with the cheat state initialised from the build-time constant
      TRAINED_CHEATS (default: infinite lives ON, everything else OFF).
      The menu module is dropped from the binary entirely.

  src/kickass/tony-trainer-romfree.asm -> tony-trainer-romfree.prg
      Same five-toggle "official trainer" menu, but rendered with the
      game's own embedded font AFTER init/unpack (cheatmenu-romfree.asm)
      instead of through the character ROM - so it displays on ROM-less
      targets such as minimal64.

Run from repo root: python3 tools/make_trainers.py
"""


def load():
    return open("src/kickass/tony.asm").read()


def sub(src, old, new, count=1):
    assert src.count(old) == count, f"anchor not found ({count}x): {old[:60]!r}"
    return src.replace(old, new)


# ------------------------------------------------- tony-trained (no menu)
src = load()
src = sub(src, '.file [name="./tony.prg"', '.file [name="./tony-trained.prg"')
src = sub(src, '#import "_loader.asm"',
          '#import "_loader.asm"\n\n'
          '// trainer configuration, baked in at assembly time\n'
          '.label TRAINED_CHEATS = CHEAT_INFINITE_LIVES')
src = sub(src, """    cli
    jsr cheatMenu
    jsr blankScreen""",
          """    cli
    lda #TRAINED_CHEATS
    sta gameCheatState
    jsr blankScreen""")
src = sub(src, """_menuBegin:
#import "cheatmenu.asm"
_menuEnd:

.assert "Cheatmenu cannot overlap with IO memory", _menuEnd < $D000, true


""", "")
src = sub(src, '.print "Cheatmenu location $" + toHexString(_menuBegin) + " - $" + toHexString(_menuEnd - 1)\n', "")
open("src/kickass/tony-trained.asm", "w").write(src)
print("wrote src/kickass/tony-trained.asm")

# --------------------------------------------- tony-trainer-romfree (menu)
src = load()
src = sub(src, '.file [name="./tony.prg"', '.file [name="./tony-trainer-romfree.prg"')
src = sub(src, """    cli
    jsr cheatMenu
    jsr blankScreen""",
          """    cli
    jsr cheatMenuRomfree
    jsr blankScreen""")
src = sub(src, '#import "cheatmenu.asm"', '#import "cheatmenu-romfree.asm"')
open("src/kickass/tony-trainer-romfree.asm", "w").write(src)
print("wrote src/kickass/tony-trainer-romfree.asm")
