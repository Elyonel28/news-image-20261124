#!/usr/bin/env python3
"""news-image-20261124 — sums up Tuesday 24 November 2026 in one image.

Pure Python 3 stdlib. Draws a 1024x1024 newspaper front page with a
hand-built 5x7 pixel font and a tiny PNG encoder (zlib + struct only).
No network, no randomness, no clock: two runs write identical bytes.

Run:  python3 main.py
Writes: entry.png next to this file, and /output/entry.png when /output exists.
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 231)
INK = (26, 26, 26)
NAVY = (20, 38, 63)
NAVY2 = (28, 52, 84)
RED = (179, 38, 30)
GOLD = (200, 147, 42)
GOLD_LT = (232, 196, 90)
WHITE = (255, 255, 255)
GREY = (107, 107, 107)
PANEL = (255, 255, 255)
BORDER = (216, 208, 188)
TEAL = (23, 94, 94)
SKY = (214, 231, 240)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = ink. Uppercase only; lowercase is
# folded to uppercase by the text helpers. Unknown chars render as blank.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", "..#..", "..#.."),
    ',': (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    ':': (".....", "..#..", ".....", ".....", ".....", "..#..", "..#.."),
    ';': (".....", "..#..", ".....", ".....", ".....", "..#..", ".#..."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", ".####", ".....", ".....", "....."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '%': ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    '&': (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    '+': (".....", "..#..", "..#..", ".####", "..#..", "..#..", "....."),
    '=': (".....", ".....", ".####", ".....", ".####", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", ".###.", "..#..", ".#.#.", "....."),
    '#': (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    '@': (".###.", "#...#", "#.###", "#.#.#", "#.##.", "#....", ".###."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    '<': ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    '>': (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    '[': (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    ']': (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    '$': ("..#..", ".####", "#.#.#", ".#...", "..##.", "...#.", "####."),
    '\\': ("#....", "#....", ".#...", "..#..", "...#.", "....#", "....#"),
    '|': ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    '~': (".....", ".....", ".##.#", "#.#.#", ".....", ".....", "....."),
    '`': ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '{': ("...##", "..#..", ".#...", ".##..", ".#...", "..#..", "...##"),
    '}': ("##...", "..#..", "...#.", "..##.", "...#.", "..#..", "##..."),
    '^': ("..#..", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    # bullet used in the ticker strip
    '\u2022': (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    # curly quotes fold onto straight ones at draw time
    '\u201c': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '\u201d': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '\u2019': ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '\u2014': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
}

CHAR_W = 6  # 5 px glyph + 1 px gap


def text_width(s, scale):
    return sum(CHAR_W for _ in s) * scale - scale


def draw_text(px, x, y, s, scale, color, align="left"):
    """Draw uppercase text. Returns the y just below the text."""
    s = s.upper()
    if align == "center":
        x -= text_width(s, scale) // 2
    elif align == "right":
        x -= text_width(s, scale)
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            x += CHAR_W * scale
            continue
        for row, line in enumerate(glyph):
            for col, cell in enumerate(line):
                if cell == '1' or cell == '#':
                    for dy in range(scale):
                        for dx in range(scale):
                            px.set(x + col * scale + dx, y + row * scale + dy, color)
        x += CHAR_W * scale
    return y + 7 * scale


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = s.upper().split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(px, x, y, s, scale, color, max_w, leading=None):
    """Draw a wrapped paragraph. Returns y below the last line."""
    if leading is None:
        leading = 7 * scale + 4
    for line in wrap_text(s, scale, max_w):
        draw_text(px, x, y, line, scale, color)
        y += leading
    return y


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def rect_outline(self, x, y, w, h, color, t=1):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line with square brush of thickness t."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                else:
                    if abs(d2 - r * r) <= r:
                        self.set(xx, yy, color)

    def poly(self, pts, color):
        """Scanline fill (even-odd) for any simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, color)

    def triangle(self, p0, p1, p2, color):
        self.poly([p0, p1, p2], color)


# ---------------------------------------------------------------- icons
def draw_scales(px, cx, y, s, color):
    """Scales of justice: pole, beam, two hanging pans, base."""
    # beam
    px.hline(cx - s // 2, y + 12, s, color, t=6)
    px.circle(cx, y + 12, 5, color)
    # pole
    px.vline(cx, y + 12, s - 40, color, t=6)
    # pans
    for side in (-1, 1):
        bx = cx + side * (s // 2 - 6)
        px.line(bx, y + 15, bx - 26, y + s // 2, color, t=3)
        px.line(bx, y + 15, bx + 26, y + s // 2, color, t=3)
        px.poly([(bx - 30, y + s // 2), (bx + 30, y + s // 2),
                 (bx + 18, y + s // 2 + 18), (bx - 18, y + s // 2 + 18)], color)
    # base
    px.rect(cx - 34, y + s - 22, 68, 8, color)
    px.rect(cx - 48, y + s - 12, 96, 8, color)


def draw_tanker(px, x, y, w, h, hull, accent):
    """Oil tanker on waves with a mine above it."""
    # mine: spiked circle
    cx, cy, r = x + w - 26, y + 16, 10
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1),
                   (-1, 1), (1, 1)):
        px.line(cx, cy, cx + dx * (r + 7), cy + dy * (r + 7), accent, t=2)
    px.circle(cx, cy, r, accent)
    px.circle(cx, cy, 3, WHITE)
    # hull
    px.poly([(x, y + h - 26), (x + w - 70, y + h - 26),
             (x + w - 40, y + h - 8), (x + 8, y + h - 8)], hull)
    # containers
    for i in range(3):
        px.rect(x + 14 + i * 34, y + h - 52, 28, 24, accent if i == 1 else hull)
    # bridge
    px.rect(x + w - 66, y + h - 58, 22, 30, hull)
    # waves
    for wy in (y + h - 4, y + h + 2):
        for wx in range(x, x + w, 16):
            px.line(wx, wy, wx + 8, wy - 4, NAVY2, t=2)
            px.line(wx + 8, wy - 4, wx + 16, wy, NAVY2, t=2)


def draw_ship_drone(px, x, y, w, h, hull, accent):
    """A warship with a small drone above it; h is the strip height."""
    # drone: body + 4 rotors
    dx, dy = x + w - 34, y + 12
    px.rect(dx - 10, dy - 5, 20, 10, INK)
    for ox, oy in ((-16, -8), (16, -8), (-16, 8), (16, 8)):
        px.line(dx + ox - 8, dy + oy, dx + ox + 8, dy + oy, INK, t=2)
        px.line(dx + ox, dy + oy, dx, dy, INK, t=2)
    # ship hull
    hull_top = y + h - 24
    px.poly([(x, hull_top), (x + w - 60, hull_top),
             (x + w - 30, y + h - 8), (x + 6, y + h - 8)], hull)
    # superstructure + mast
    px.rect(x + 40, hull_top - 20, 46, 20, hull)
    px.vline(x + 62, hull_top - 38, 20, hull, t=4)
    px.rect(x + 30, hull_top - 14, 10, 14, accent)
    # explosion starburst on the bow
    ex, ey = x + w - 44, hull_top - 6
    for k in range(8):
        ang = k * 3.14159 / 4
        px.line(ex, ey, int(ex + 16 * (1 if k % 2 == 0 else 0.6) * __import__('math').cos(ang)),
                int(ey + 16 * (1 if k % 2 == 0 else 0.6) * __import__('math').sin(ang)),
                GOLD, t=3)
    px.circle(ex, ey, 6, RED)
    # waves
    for wx in range(x, x + w, 16):
        px.line(wx, y + h - 2, wx + 8, y + h - 6, NAVY2, t=2)
        px.line(wx + 8, y + h - 6, wx + 16, y + h - 2, NAVY2, t=2)


def draw_trophy(px, x, y, s, gold, ink):
    """A winners' cup."""
    # cup body
    px.poly([(x, y), (x + s, y), (x + s * 4 // 5, y + s // 2),
             (x + s // 5, y + s // 2)], gold)
    # handles
    px.line(x, y + 4, x - s // 5, y + s // 4, gold, t=4)
    px.line(x - s // 5, y + s // 4, x + s // 10, y + s // 2, gold, t=4)
    px.line(x + s, y + 4, x + s * 6 // 5, y + s // 4, gold, t=4)
    px.line(x + s * 6 // 5, y + s // 4, x + s * 9 // 10, y + s // 2, gold, t=4)
    # stem + base
    px.rect(x + s // 2 - 3, y + s // 2, 6, s // 4, gold)
    px.rect(x + s // 5, y + s * 3 // 4, s * 3 // 5, 5, gold)
    px.rect(x + s // 10, y + s * 3 // 4 + 7, s * 4 // 5, 5, ink)


def draw_rocket(px, x, y, s, body, flame):
    """A rocket lifting off."""
    # body
    px.poly([(x + s // 2, y), (x + s * 3 // 4, y + s // 4),
             (x + s * 3 // 4, y + s * 3 // 4), (x + s // 4, y + s * 3 // 4),
             (x + s // 4, y + s // 4)], body)
    # window
    px.circle(x + s // 2, y + s // 3, s // 10, SKY)
    px.circle(x + s // 2, y + s // 3, s // 10, SKY)
    # fins
    px.triangle((x + s // 4, y + s * 3 // 5), (x + s // 4, y + s * 7 // 8),
                (x + s // 12, y + s * 7 // 8), RED)
    px.triangle((x + s * 3 // 4, y + s * 3 // 5), (x + s * 3 // 4, y + s * 7 // 8),
                (x + s * 11 // 12, y + s * 7 // 8), RED)
    # flame
    px.triangle((x + s * 3 // 8, y + s * 7 // 8), (x + s * 5 // 8, y + s * 7 // 8),
                (x + s // 2, y + s), flame)


def draw_chart(px, x, y, w, h, color):
    """A line chart: up, then a sharp fall, then a small recovery."""
    pts = [(x, y + h // 3), (x + w // 4, y + h // 6),
           (x + w // 2, y + h // 4), (x + w * 3 // 4, y + h - 8),
           (x + w - 2, y + h * 2 // 3)]
    for a, b in zip(pts, pts[1:]):
        px.line(a[0], a[1], b[0], b[1], color, t=3)
    for p in pts:
        px.circle(p[0], p[1], 3, color)
    px.vline(x, y, h, GREY, t=1)
    px.hline(x, y + h - 1, w, GREY, t=1)


# ---------------------------------------------------------------- PNG writer
def png_bytes(px):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += px.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- layout
def build():
    px = Canvas(W, H, PAPER)

    # ---- masthead
    px.rect(0, 0, W, 138, NAVY)
    draw_text(px, W // 2, 18, "THE WORLD IN ONE DAY", 8, WHITE, align="center")
    px.hline(120, 96, W - 240, GOLD, t=3)
    draw_text(px, W // 2, 108, "TUESDAY  -  24 NOVEMBER 2026", 4, GOLD_LT, align="center")

    # ---- lead story: Huawei verdict
    y = 152
    px.rect(28, y, 968, 340, PANEL)
    px.rect_outline(28, y, 968, 340, BORDER, t=2)
    draw_text(px, 48, y + 16, "HUAWEI GUILTY", 8, RED)
    draw_text(px, 48, y + 88, "U.S. JURY CONVICTS HUAWEI", 4, INK)
    lead_body = ("Jurors found Huawei guilty on 10 of 12 counts, "
                 "including stealing trade secrets and bank fraud, "
                 "after a two-month trial. Cleared of racketeering; "
                 "the company will appeal.")
    draw_para(px, 48, y + 126, lead_body, 3, INK, 600)
    draw_text(px, 48, y + 306, "SENTENCING SET FOR SEPTEMBER 2027", 2, GREY)
    # scales of justice illustration, right side
    px.rect(700, y + 24, 276, 292, SKY)
    px.rect_outline(700, y + 24, 276, 292, BORDER, t=2)
    draw_scales(px, 838, y + 52, 190, NAVY)
    draw_text(px, 838, y + 252, "10 OF 12 COUNTS", 3, RED, align="center")

    # ---- row 2: two half-width panels, icon strip at the bottom
    y2 = 506
    # Hormuz
    px.rect(28, y2, 477, 200, PANEL)
    px.rect_outline(28, y2, 477, 200, BORDER, t=2)
    px.rect(28, y2, 477, 6, RED)
    draw_text(px, 48, y2 + 14, "STRAIT OF HORMUZ", 4, INK)
    draw_text(px, 48, y2 + 48, "FOUR TANKERS HIT BY MINES", 3, RED)
    draw_para(px, 48, y2 + 76,
              "Iran says four tankers struck mines and its navy "
              "attacked a container ship in the strait.", 2, INK, 440)
    draw_tanker(px, 48, y2 + 140, 437, 54, NAVY, RED)
    # Ukraine
    px.rect(519, y2, 477, 200, PANEL)
    px.rect_outline(519, y2, 477, 200, BORDER, t=2)
    px.rect(519, y2, 477, 6, NAVY)
    draw_text(px, 539, y2 + 14, "WAR SPREADS", 4, INK)
    draw_text(px, 539, y2 + 48, "UKRAINE HITS RUSSIAN SHIPS", 3, RED)
    draw_para(px, 539, y2 + 76,
              "Drones hit Russian ships in the Gulf of Finland and "
              "off Libya. Poland cites a new airspace violation.",
              2, INK, 440)
    draw_ship_drone(px, 539, y2 + 140, 437, 54, NAVY, RED)

    # ---- row 3: three panels
    y3 = 720
    pw, gap = 315, 11
    panels = [
        (28, "SENEGAL", "CHAMPIONS AGAIN",
         "Court gives the Africa Cup title back to Senegal. "
         "Morocco vows to appeal.", "trophy"),
        (28 + pw + gap, "SPACE", "FIRST FOREIGNER ABOARD TIANGONG",
         "China's Shenzhou-24 carries Pakistan's Zeeshan Ali "
         "to the station.", "rocket"),
        (28 + 2 * (pw + gap), "MARKETS", "NVIDIA DOWN, CONFIDENCE UP",
         "Nvidia falls 6% as the Huang rally fades. U.S. "
         "confidence at a near two-year high.", "chart"),
    ]
    for x, kicker, head, body, kind in panels:
        px.rect(x, y3, pw, 188, PANEL)
        px.rect_outline(x, y3, pw, 188, BORDER, t=2)
        px.rect(x, y3, pw, 4, GOLD)
        draw_text(px, x + 16, y3 + 14, kicker, 2, RED)
        draw_para(px, x + 16, y3 + 36, head, 3, INK, pw - 32)
        if kind == "trophy":
            draw_trophy(px, x + pw - 78, y3 + 118, 44, GOLD, INK)
            draw_para(px, x + 16, y3 + 92, body, 2, INK, pw - 110)
        elif kind == "rocket":
            draw_rocket(px, x + pw - 62, y3 + 112, 56, NAVY, GOLD)
            draw_para(px, x + 16, y3 + 92, body, 2, INK, pw - 92)
        else:
            draw_chart(px, x + pw - 100, y3 + 12, 84, 30, RED)
            draw_para(px, x + 16, y3 + 92, body, 2, INK, pw - 32)

    # ---- ticker strip
    y4 = 922
    px.rect(28, y4, 968, 56, NAVY)
    draw_text(px, 44, y4 + 8,
              "ALSO TODAY: TURKISH HELICOPTER CRASH KILLS 5 \u2022 "
              "25 HOSTAGES IN CARTAGENA", 2, WHITE)
    draw_text(px, 44, y4 + 30,
              "HANOI BLAST KILLS 6 \u2022 HASINA TO RETURN DEC 16 \u2022 "
              "UN: 5 WOMEN KILLED EVERY HOUR", 2, GOLD_LT)

    # ---- footer
    draw_text(px, W // 2, 990,
              "SOURCES: REUTERS, AP, UN NEWS - ALL STORIES FIRST "
              "REPORTED TUESDAY 24 NOVEMBER 2026",
              2, GREY, align="center")

    return px


def main():
    px = build()
    data = png_bytes(px)
    here = os.path.dirname(os.path.abspath(__file__))
    out_local = os.path.join(here, "entry.png")
    with open(out_local, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (out_local, len(data)))
    if os.path.isdir("/output"):
        with open("/output/entry.png", "wb") as f:
            f.write(data)
        print("wrote /output/entry.png (%d bytes)" % len(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
