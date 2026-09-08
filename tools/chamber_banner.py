#!/usr/bin/env python3
"""
chamber_banner.py - the Chamber itself as a vector image, for the collection's public page: an emulator
framebuffer (a PPM or PNG from the harness's shot: command) becomes an SVG of pixel runs, one path per
colour, exactly the game's pixels; then compositions for a marketplace: a wide banner with the room
centred ("zoomed out"), a square collection image and a featured image, each as SVG and as PNG.

    python3 tools/chamber_banner.py FRAME.ppm --out deliverables/assets/banner
"""
import argparse, io, os, sys
from collections import Counter
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buddy_thumbnail as bt

ORIGIN = (32, 40)          # the visible 320 x 200 screen inside minimal64's 384 x 284 frame
SIZE = (320, 200)
EXE = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

def room_paths(im):
    """One path per colour of the 320 x 200 screen, as pixel runs; black is the background."""
    px = im.load(); w, h = im.size
    colours = [c for c, _ in Counter(im.getdata()).most_common() if c != (0, 0, 0)]
    parts = []
    for c in colours:
        mask = [[1 if px[x, y] == c else 0 for x in range(w)] for y in range(h)]
        parts.append(f'<path fill="#{c[0]:02x}{c[1]:02x}{c[2]:02x}" d="{bt.runs_path(mask, 0, 0)}"/>')
    return "\n".join(parts)

def room_svg(paths):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE[0]} {SIZE[1]}" shape-rendering="crispEdges">\n'
            f'<rect width="{SIZE[0]}" height="{SIZE[1]}" fill="#000"/>\n{paths}\n</svg>\n')

def composed_svg(paths, W, H, scale, dx=None, dy=None):
    """The room at a scale inside a black W x H canvas, centred unless dx, dy are given."""
    rw, rh = SIZE[0] * scale, SIZE[1] * scale
    dx = (W - rw) / 2 if dx is None else dx; dy = (H - rh) / 2 if dy is None else dy
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" shape-rendering="crispEdges">\n'
            f'<rect width="{W}" height="{H}" fill="#000"/>\n<g transform="translate({dx:g} {dy:g}) scale({scale:g})">\n{paths}\n</g>\n</svg>\n')

def render_png(svg_path, png_path, W, H):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE if os.path.exists(EXE) else None)
        pg = b.new_page(viewport={"width": W, "height": H}); pg.goto("file://" + os.path.abspath(svg_path)); pg.wait_for_timeout(200)
        pg.evaluate("() => { const s=document.querySelector('svg'); s.setAttribute('width', innerWidth); s.setAttribute('height', innerHeight); }")
        pg.wait_for_timeout(60); pg.screenshot(path=png_path); b.close()
    print(f"{png_path}: {W}x{H}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frame"); ap.add_argument("--out", default="deliverables/assets/banner")
    ap.add_argument("--origin", nargs=2, type=int, default=ORIGIN)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    im = Image.open(a.frame).convert("RGB")
    if im.size != SIZE: im = im.crop((a.origin[0], a.origin[1], a.origin[0] + SIZE[0], a.origin[1] + SIZE[1]))
    paths = room_paths(im)
    outs = [("chamber-room.svg", room_svg(paths), 1280, 800),
            ("chamber-banner-1400x350.svg", composed_svg(paths, 1400, 350, 1.75), 1400, 350),          # the room centred, 560 x 350
            ("chamber-collection-1000x1000.svg", composed_svg(paths, 1000, 1000, 3), 1000, 1000),      # the room 960 x 600, centred
            ("chamber-featured-600x400.svg", composed_svg(paths, 600, 400, 1.875), 600, 400)]           # the room 600 x 375, centred
    for name, doc, W, H in outs:
        p = os.path.join(a.out, name); open(p, "w").write(doc); print(f"{p}: {os.path.getsize(p)} bytes")
        render_png(p, p[:-4] + ".png", W, H)
    im.save(os.path.join(a.out, "chamber-room-320x200.png")); print("runs:", paths.count("M"))

if __name__ == "__main__":
    main()
