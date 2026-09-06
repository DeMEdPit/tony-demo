/*
 * MIT License - Copyright (c) 2023 Maciej Malecki (tony-demo tooling)
 *
 * Headless test harness for the minimal64 emulator (nopsta 2022).
 * Boots a PRG on minimal64 exactly as the web build would and executes a
 * small command script so builds can be verified on the ROM-free target:
 *
 *   ./m64run GAME.PRG "wait:120,shot:a.ppm,joy:16:25,key:43:5,peek:2d"
 *   ./m64run GAME.PRG @script.txt          (the same commands from a file; newlines count as commas)
 *
 * commands: wait:N        run N PAL frames
 *           shot:FILE     dump the pixel buffer as binary PPM
 *           joy:MASK:N    hold joystick-2 lines MASK for N frames (then release, +5 frames)
 *           hold:MASK     press joystick-2 lines MASK and leave them pressed
 *           release:MASK  release joystick-2 lines MASK (no frames run: pair with wait:N)
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
extern void m64_audioInit(uint32_t bufferLength, uint32_t sampleRate);
extern int32_t m64_getAudioSamplesAvailable(void);
extern unsigned char *m64_getAudioBuffer(void);
extern void sid_update(void);
extern uint32_t SIDAUDIOBUFFERLENGTH;

/* audio:FILE writes everything the SID plays from then on as a 16-bit mono WAV at 44.1 kHz */
static FILE *wav = NULL;
static uint32_t wavSamples = 0;
static void wavHeader(FILE *f, uint32_t samples) {
    uint32_t rate = 44100, bytes = samples * 2, chunk = 36 + bytes, fmt = 16, byteRate = rate * 2;
    uint16_t pcm = 1, ch = 1, align = 2, bits = 16;
    fseek(f, 0, SEEK_SET);
    fwrite("RIFF", 1, 4, f); fwrite(&chunk, 4, 1, f); fwrite("WAVEfmt ", 1, 8, f); fwrite(&fmt, 4, 1, f);
    fwrite(&pcm, 2, 1, f); fwrite(&ch, 2, 1, f); fwrite(&rate, 4, 1, f); fwrite(&byteRate, 4, 1, f);
    fwrite(&align, 2, 1, f); fwrite(&bits, 2, 1, f); fwrite("data", 1, 4, f); fwrite(&bytes, 4, 1, f);
}
static void wavDrain(void) {
    if (!wav) return;
    sid_update();                                   /* clock the SID up to now */
    while (m64_getAudioSamplesAvailable() >= (int32_t)SIDAUDIOBUFFERLENGTH) {
        float *b = (float *)m64_getAudioBuffer();
        for (uint32_t i = 0; i < SIDAUDIOBUFFERLENGTH; i++) {
            float v = b[i] * 0.75f;                  /* the emulator's scale peaks just over full scale; leave headroom */
            if (v > 1.0f) v = 1.0f; if (v < -1.0f) v = -1.0f;
            int16_t s = (int16_t)(v * 32767.0f);
            fwrite(&s, 2, 1, wav);
        }
        wavSamples += SIDAUDIOBUFFERLENGTH;
    }
}
static void wavClose(void) {
    if (!wav) return;
    wavDrain();
    wavHeader(wav, wavSamples);
    fclose(wav); wav = NULL;
    printf("wav: %u samples (%.1f s)\n", wavSamples, wavSamples / 44100.0);
}
extern uint32_t harness_getPC(void);

static void frames(int n) {
    for (int i = 0; i < n; i++) { m64_update(20); wavDrain(); } /* ~1 PAL frame per call */
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

    char *script;
    if (argv[2][0] == '@') {                 /* @FILE: read the script from a file (long scripts exceed argv) */
        FILE *sf = fopen(argv[2] + 1, "rb");
        if (!sf) { perror("script"); return 1; }
        fseek(sf, 0, SEEK_END);
        long slen = ftell(sf);
        fseek(sf, 0, SEEK_SET);
        script = malloc(slen + 1);
        slen = fread(script, 1, slen, sf);
        script[slen] = 0;
        fclose(sf);
        for (char *c = script; *c; c++) if (*c == '\n' || *c == '\r') *c = ',';
    } else {
        script = strdup(argv[2]);
    }
    for (char *cmd = strtok(script, ","); cmd; cmd = strtok(NULL, ",")) {
        if (!strncmp(cmd, "wait:", 5)) {
            frames(atoi(cmd + 5));
        } else if (!strncmp(cmd, "shot:", 5)) {
            shot(cmd + 5);
        } else if (!strncmp(cmd, "hold:", 5)) {
            m64_joystickPush(1, atoi(cmd + 5));
        } else if (!strncmp(cmd, "release:", 8)) {
            m64_joystickRelease(1, atoi(cmd + 8));
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
        } else if (!strncmp(cmd, "audio:", 6)) {   /* audio:FILE  start writing a WAV of the SID output */
            wavClose();
            m64_audioInit(1024, 44100);
            wav = fopen(cmd + 6, "wb"); wavSamples = 0;
            if (wav) { uint8_t zero[44] = {0}; fwrite(zero, 1, 44, wav); }
        } else if (!strcmp(cmd, "audio-stop")) {
            wavClose();
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
    wavClose();
    return 0;
}
