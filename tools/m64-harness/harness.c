/*
 * MIT License - Copyright (c) 2023 Maciej Malecki (tony-demo tooling)
 *
 * Headless test harness for the minimal64 emulator (nopsta 2022).
 * Boots a PRG on minimal64 exactly as the web build would and executes a
 * small command script so builds can be verified on the ROM-free target:
 *
 *   ./m64run GAME.PRG "wait:120,shot:a.ppm,joy:16:25,key:43:5,peek:2d"
 *
 * commands: wait:N        run N PAL frames
 *           shot:FILE     dump the pixel buffer as binary PPM
 *           joy:MASK:N    hold joystick-2 lines MASK for N frames
 *           key:CODE:N    hold key CODE (keyboard.h codes) for N frames
 *           peek:HEX      print one byte of CPU-visible memory
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

extern void m64_init(int32_t model, int32_t sidModel);
extern void m64_injectAndRunPrg(uint8_t *data, uint32_t len, uint32_t delay);
extern int32_t m64_update(int32_t deltaTime);
extern unsigned char *m64_getPixelBuffer(void);
extern uint32_t m64_getPixelBufferWidth(void);
extern uint32_t m64_getPixelBufferHeight(void);
extern void m64_keyPush(uint32_t key);
extern void m64_keyRelease(uint32_t key);
extern void m64_joystickPush(uint32_t joystick, uint32_t direction);
extern void m64_joystickRelease(uint32_t joystick, uint32_t direction);
extern uint8_t m64_cpuRead(uint16_t address);
extern uint32_t harness_getPC(void);

static void frames(int n) {
    for (int i = 0; i < n; i++) m64_update(20); /* ~1 PAL frame per call */
}

static void shot(const char *path) {
    uint32_t w = m64_getPixelBufferWidth(), h = m64_getPixelBufferHeight();
    uint32_t *px = (uint32_t *)m64_getPixelBuffer();
    FILE *f = fopen(path, "wb");
    fprintf(f, "P6\n%u %u\n255\n", w, h);
    for (uint32_t i = 0; i < w * h; i++) {
        uint32_t p = px[i];
        fputc(p & 0xff, f);          /* stored little-endian RGBA */
        fputc((p >> 8) & 0xff, f);
        fputc((p >> 16) & 0xff, f);
    }
    fclose(f);
    printf("shot %s (%ux%u)\n", path, w, h);
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s prg script\n", argv[0]); return 1; }
    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror("prg"); return 1; }
    static uint8_t prg[70000];
    uint32_t len = (uint32_t)fread(prg, 1, sizeof prg, f);
    fclose(f);
    printf("prg %s: %u bytes\n", argv[1], len);

    m64_init(1 /* PAL */, 0);
    m64_injectAndRunPrg(prg, len, 0);

    char *script = strdup(argv[2]);
    for (char *cmd = strtok(script, ","); cmd; cmd = strtok(NULL, ",")) {
        if (!strncmp(cmd, "wait:", 5)) {
            frames(atoi(cmd + 5));
        } else if (!strncmp(cmd, "shot:", 5)) {
            shot(cmd + 5);
        } else if (!strncmp(cmd, "joy:", 4)) {
            uint32_t mask = (uint32_t)strtoul(cmd + 4, NULL, 10);
            char *n = strchr(cmd + 4, ':');
            m64_joystickPush(1, mask);          /* joystick in port 2 */
            frames(n ? atoi(n + 1) : 10);
            m64_joystickRelease(1, mask);
            frames(5);
        } else if (!strncmp(cmd, "key:", 4)) {
            uint32_t key = (uint32_t)strtoul(cmd + 4, NULL, 10);
            char *n = strchr(cmd + 4, ':');
            m64_keyPush(key);
            frames(n ? atoi(n + 1) : 5);
            m64_keyRelease(key);
            frames(5);
        } else if (!strcmp(cmd, "pc")) {
            printf("pc ~ $%04x\n", harness_getPC());
        } else if (!strncmp(cmd, "peek:", 5)) {
            uint16_t a = (uint16_t)strtoul(cmd + 5, NULL, 16);
            printf("peek $%04x = $%02x\n", a, m64_cpuRead(a));
        } else if (!strncmp(cmd, "dump:", 5)) {   /* dump:ADDRHEX:LENHEX:FILE  raw CPU-visible bytes */
            uint16_t a = (uint16_t)strtoul(cmd + 5, NULL, 16);
            char *l = strchr(cmd + 5, ':');
            uint32_t n = l ? (uint32_t)strtoul(l + 1, NULL, 16) : 0;
            char *path = l ? strchr(l + 1, ':') : NULL;
            if (path) {
                FILE *o = fopen(path + 1, "wb");
                for (uint32_t i = 0; i < n && o; i++) fputc(m64_cpuRead((uint16_t)(a + i)), o);
                if (o) fclose(o);
                printf("dump $%04x +%u -> %s\n", a, n, path + 1);
            }
        } else if (!strncmp(cmd, "poke:", 5)) {   /* poke:ADDRHEX:VALHEX */
            uint16_t a = (uint16_t)strtoul(cmd + 5, NULL, 16);
            char *v = strchr(cmd + 5, ':');
            uint8_t val = (uint8_t)strtoul(v ? v + 1 : "0", NULL, 16);
            m64_cpuWrite(a, val);
            printf("poke $%04x <- $%02x\n", a, val);
        }
    }
    return 0;
}
