#!/usr/bin/env python3
"""
motion_show.py - a motion demo for a video: all axes, laser off

  python tools/motion_show.py --preview      write the G-code and a picture of the path, no motion
  python tools/motion_show.py --run          home, then run it (machine idle, USB free)
  python tools/motion_show.py --run --power  60 s of all axes accelerating at once (current draw)

The path stays inside X 30..250, Y 25..205, Z -10..-80 (machine coordinates). The laser stays off
(M5, S0), so nothing is burned. Stop with feed hold on the display or the gamepad (Circle).
"""

import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CX, CY = 140.0, 115.0           # centre of the show
ZT, ZB = -10.0, -80.0           # Z top and bottom
F_FAST, F_MID = 4500, 3000


def build():
    g = ['G21 G90 M5 S0', 'G53 G0 Z%g' % ZT, 'G53 G0 X%g Y%g' % (CX, CY)]
    xy = lambda x, y, f: 'G53 G1 X%.3f Y%.3f F%d' % (x, y, f)
    xyz = lambda x, y, z, f: 'G53 G1 X%.3f Y%.3f Z%.3f F%d' % (x, y, z, f)

    # 1. rapid square and its diagonals
    for x, y in ((CX - 100, CY - 80), (CX + 100, CY - 80), (CX + 100, CY + 80), (CX - 100, CY + 80),
                 (CX - 100, CY - 80), (CX + 100, CY + 80), (CX + 100, CY - 80), (CX - 100, CY + 80), (CX, CY)):
        g.append('G53 G0 X%g Y%g' % (x, y))

    # 2. Z bounce in the centre, faster and faster
    for depth, f in ((-40, 800), (-60, 1100), (-80, 1500)):
        g.append('G53 G1 Z%g F%d' % (depth, f))
        g.append('G53 G1 Z%g F%d' % (ZT, f))

    # 3. growing circles (G2 in machine coordinates through G53 is not allowed: work offsets are zero
    #    in this program's use, so plain arcs are written as line segments instead)
    for r in (20, 40, 60, 80):
        n = int(r * 1.2)
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            g.append(xy(CX + r * math.cos(a), CY + r * math.sin(a), F_MID + r * 15))

    # 4. spiral inwards while Z goes down
    turns, steps = 5, 300
    for i in range(steps + 1):
        t = i / steps
        a = 2 * math.pi * turns * t
        r = 80 * (1 - t)
        g.append(xyz(CX + r * math.cos(a), CY + r * math.sin(a), ZT + (ZB - ZT) * t, F_MID))

    # 5. Lissajous figure 3:2 with Z waving
    steps = 400
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        g.append(xyz(CX + 100 * math.sin(3 * t), CY + 80 * math.sin(2 * t),
                     (ZT + ZB) / 2 + (ZT - ZB) / 2 * math.cos(4 * t), F_FAST))

    # 6. five-pointed star, twice, fast
    g.append('G53 G0 Z%g' % ZT)
    pts = [(CX + 85 * math.sin(2 * math.pi * k * 2 / 5), CY + 85 * math.cos(2 * math.pi * k * 2 / 5)) for k in range(6)]
    for _ in range(2):
        for x, y in pts:
            g.append(xy(x, y, F_FAST))

    # 7. zigzag across the table
    for k in range(9):
        y = CY - 80 + k * 20
        g.append(xy(CX - 100 if k % 2 == 0 else CX + 100, y, F_FAST))

    # back to the centre, Z up
    g += ['G53 G0 Z%g' % ZT, 'G53 G0 X%g Y%g' % (CX, CY), 'M5']
    return g


def preview(lines):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    pts, cur = [], [CX, CY, ZT]
    for l in lines:
        for w in l.split():
            if w[0] in 'XYZ' and w[1:].replace('.', '').replace('-', '').isdigit():
                cur['XYZ'.index(w[0])] = float(w[1:])
        pts.append(tuple(cur))
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(projection='3d')
    xs, ys, zs = zip(*pts)
    ax.plot(xs, ys, zs, lw=0.8, color='#7b5cff')
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title('motion show: %d lines' % len(lines))
    out = os.path.join(HERE, 'motion_show.png')
    plt.savefig(out, dpi=90)
    print('picture:', out)


def run(lines):
    import serial, serial.tools.list_ports
    port = next((p.device for p in serial.tools.list_ports.comports() if p.vid == 0x0483 and p.pid == 0x5740), None)
    if not port:
        sys.exit('Board not found on USB.')
    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(0.3)
    ser.reset_input_buffer()

    def send(l, timeout=120):
        ser.write((l + '\n').encode())
        end = time.time() + timeout
        while time.time() < end:
            r = ser.readline().decode(errors='replace').strip()
            if r == 'ok':
                return True
            if r.startswith('error') or r.startswith('ALARM'):
                print(l, '->', r)
                return False
        return False

    if not send('$H'):
        sys.exit('Homing failed')
    t0 = time.time()
    for l in lines:
        if not send(l):
            break
    while True:                                     # wait until the moves are done
        ser.reset_input_buffer()
        ser.write(b'?')
        s = ser.readline().decode(errors='replace').strip()
        if s.startswith('<Idle') or s.startswith('<Alarm'):
            break
        time.sleep(0.3)
    print('done in %.0f s: %s' % (time.time() - t0, s))
    ser.dtr = False


def build_power(seconds=60):
    """All axes accelerate and brake at the same time, again and again: the highest current draw."""
    pts = [(CX - 50, CY - 50, -15), (CX + 50, CY + 50, -40), (CX - 50, CY + 50, -15), (CX + 50, CY - 50, -40)]
    g = ['G21 G90 M5 S0', 'G53 G0 Z%g' % ZT, 'G53 G0 X%g Y%g' % pts[0][:2], 'G53 G0 Z%g' % pts[0][2]]
    for k in range(int(seconds / 1.5)):                 # about 1.5 s per move
        g.append('G53 G0 X%g Y%g Z%g' % pts[(k + 1) % 4])
    g += ['G53 G0 Z%g' % ZT, 'G53 G0 X%g Y%g' % (CX, CY), 'M5']
    return g


if __name__ == '__main__':
    lines = build_power() if '--power' in sys.argv else build()
    with open(os.path.join(HERE, 'motion_show.nc'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    if '--run' in sys.argv:
        run(lines)
    else:
        preview(lines)
