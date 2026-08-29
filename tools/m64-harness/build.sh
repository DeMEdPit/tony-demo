#!/bin/sh
# Build the headless minimal64 test runner. Usage: build.sh /path/to/minimal64
# Copies the emulator sources and renames its timer_t typedef, which
# collides with the glibc timer_t when compiling natively.
set -e
M=${1:-/home/user/demedpit/minimal64}
B=tools/m64-harness/.build-src
rm -rf $B && mkdir -p $B && cp -r $M/src/* $B/
find $B -name '*.c' -o -name '*.h' | xargs sed -i "s/\\btimer_t\\b/m64timer_t/g; s/\\bkey_t\\b/m64key_t/g; s/\\bclock_t\\b/m64clock_t/g"
cat > $B/pcprobe.c <<'EOP'
#include "m64.h"
uint32_t harness_getPC(void) { return m64_cpu.Register_ProgramCounter; }
EOP
gcc -O2 -w -I$B -o tools/m64-harness/m64run tools/m64-harness/harness.c \
  $B/m64.c $B/pcprobe.c $B/memory/*.c $B/cartridge/cartridge.c \
  $B/clock/clock.c $B/iec/iecBus.c $B/joystick/joystick.c \
  $B/keyboard/keyboard.c $B/vic/*.c $B/cpu/m6510.c \
  $B/cia/*.c $B/sid/*.c -lm
echo built tools/m64-harness/m64run
