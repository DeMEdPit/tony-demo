#!/bin/sh
# Assembles a Chamber variant by hand with the settings build.gradle.kts uses (run from the repo root,
# after one Gradle build has populated build/): tools/build_demo.sh tony-build
set -e
V=${1:-tony-build}
cd src/kickass && java -jar ../../.ra/asms/ka/5.25/KickAss.jar "$V.asm" -libdir ../../.ra/deps/c64lib -libdir ../../build/charpad -libdir ../../build/spritepad -libdir ../../build/goattracker -libdir ../../build/sprites -libdir ../music -libdir ../level-custom :version= :variant=e -symbolfile -showmem 2>&1 | grep -v "^Picked up\|OK\. |" | grep -i "error\|size\|End of\|Music\|Intro\|wrote\|\.prg" ; ls -la "$V.prg" | awk '{print $5, $9}'
