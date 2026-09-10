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
 * commands: wait:N        run exactly N PAL frames, stopping at raster line 0 (the frame boundary)
 *           shot:FILE     dump the pixel buffer as binary PPM
 *           joy:MASK:N    hold joystick-2 lines MASK for N frames (then release, +5 frames)
 *           hold:MASK     press joystick-2 lines MASK and leave them pressed
 *           release:MASK  release joystick-2 lines MASK (no frames run: pair with wait:N)
 *           sync          run on to the next raster line 0 unless already there (wait leaves the machine
 *                         there): a peek then sees whole frames, and a poke lands before the frame's handlers
 *           snapshot      keep the machine as it is now; every later restore returns to it (the process
 *                         forks: the commands up to the next restore run in a child, then the parent goes
 *                         on from the snapshot with the commands after that restore)
 *           restore       back to the snapshot (ends the child); the commands after it start from the snapshot
 *           load:ADDRHEX:FILE   write a file's bytes into memory at the address (weights in one line)
 *   In a script file (@FILE) each line is a command and a line starting with # is a comment.
 *   With - as the script the harness reads lines from stdin, runs each (commands separated by commas)
 *   and answers "ok" on a line of its own when the line is done, so a program can drive the machine
 *   step by step and decide as it goes (snapshot and restore work within a line, not across lines).
 *           key:CODE:N    hold key CODE (keyboard.h codes) for N frames
 *           peek:HEX      print one byte of CPU-visible memory
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/wait.h>
#include "m64.h"
#include "vic/vic.h"

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
extern void clock_step(m64clock_t *clock);
extern void sid_update(void);

/* run until the raster wraps to line 0: exactly one frame from the last such point, and a place where
   neither interrupt handler is running (the top handler is about to start), so peeks see whole frames
   and pokes land before the frame's handlers. The pixel buffer is refreshed there for shot. */
static int atFrameStart = 0;
static void runToFrameStart(void) {
    int32_t was = vic_rasterY;
    for (;;) {
        clock_step(&m64_clock);
        sid_update();
        if (vic_rasterY == 0 && was != 0) break;
        was = vic_rasterY;
    }
    memcpy(vic_pixelBuffer, vic_pixels, sizeof(uint32_t) * VIC_PIXELS_LENGTH);
    atFrameStart = 1;
}
static void frames(int n) {
    for (int i = 0; i < n; i++) { runToFrameStart(); wavDrain(); }
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

static void runCommands(char *script);
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

    if (!strcmp(argv[2], "-")) {             /* interactive: one line at a time from stdin */
        char line[65536];
        while (fgets(line, sizeof line, stdin)) {
            size_t n = strlen(line);
            while (n && (line[n - 1] == '\n' || line[n - 1] == '\r')) line[--n] = 0;
            if (n == 0 || line[0] == '#') { printf("ok\n"); fflush(stdout); continue; }
            runCommands(strdup(line));
            printf("ok\n"); fflush(stdout);
        }
        wavClose();
        return 0;
    }
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
        /* a line whose first character is # is a comment */
        { char *w = script; int lineStart = 1;
          for (char *c = script; *c; c++) {
              if (lineStart && *c == '#') { while (*c && *c != '\n') c++; if (!*c) break; }
              lineStart = (*c == '\n');
              *w++ = *c;
          }
          *w = 0; }
        for (char *c = script; *c; c++) if (*c == '\n' || *c == '\r') *c = ',';
    } else {
        script = strdup(argv[2]);
    }
    runCommands(script);
    wavClose();
    return 0;
}

/* run a script: commands separated by commas; snapshot forks for the commands up to the next restore */
static void runCommands(char *script) {
    /* the script as a list of commands, so snapshot can skip ahead */
    int ncmd = 0; char **cmds = malloc(sizeof(char *) * (strlen(script) / 2 + 2));
    for (char *cmd = strtok(script, ","); cmd; cmd = strtok(NULL, ",")) cmds[ncmd++] = cmd;
    int inChild = 0;
    for (int ci = 0; ci < ncmd; ci++) {
        char *cmd = cmds[ci];
        if (!strcmp(cmd, "snapshot")) {          /* fork: the child runs on to the matching restore, the parent waits */
            fflush(stdout);
            int next = ci + 1;
            for (;;) {
                pid_t pid = fork();
                if (pid == 0) { inChild = 1; ci = next - 1; break; }          /* the child continues after the snapshot */
                int st; waitpid(pid, &st, 0);
                /* find the restore the child stopped at */
                while (next < ncmd && strcmp(cmds[next], "restore")) next++;
                if (next >= ncmd) { ci = ncmd; break; }                       /* no restore left: done */
                next++;                                                        /* the commands after that restore */
                if (next >= ncmd) { ci = ncmd; break; }
                /* another restore ahead? then fork again for the next episode; otherwise run the tail here */
                int more = 0; for (int k = next; k < ncmd; k++) if (!strcmp(cmds[k], "restore")) { more = 1; break; }
                if (!more) { ci = next - 1; break; }
            }
            if (inChild) continue;
            continue;
        } else if (!strcmp(cmd, "restore")) {
            fflush(stdout);
            if (inChild) { wavClose(); _exit(0); }
            continue;                                /* a restore without a snapshot: nothing to return to */
        } else if (!strncmp(cmd, "load:", 5)) {      /* load:ADDRHEX:FILE */
            uint16_t a = (uint16_t)strtoul(cmd + 5, NULL, 16);
            char *path = strchr(cmd + 5, ':');
            FILE *lf = path ? fopen(path + 1, "rb") : NULL;
            if (!lf) { printf("load: cannot open %s\n", path ? path + 1 : "?"); continue; }
            int c, n = 0;
            while ((c = fgetc(lf)) != EOF) { m64_cpuWrite((uint16_t)(a + n), (uint8_t)c); n++; }
            fclose(lf);
            printf("load $%04x +%d <- %s\n", a, n, path + 1);
            continue;
        }
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
        } else if (!strcmp(cmd, "sync")) {
            if (!atFrameStart) runToFrameStart();
            printf("sync raster %d\n", vic_rasterY);
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
    free(cmds);
}
