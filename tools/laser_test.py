#!/usr/bin/env python3
"""
laser_test.py - material test grid for the laser: power over speed, filled squares

  python tools/laser_test.py              write laser_test.nc only
  python tools/laser_test.py --run        stream it (machine already homed, USB free, no homing here
                                          so the hand-set Z focus stays)
  --frame                                 trace the outline with the laser off (does it fit?)
  --x 40 --y 40                           start corner in machine coordinates (default 40 / 40)

Columns: power 30..90 % (6 steps), rows: speed 1500..4500 mm/min (5 steps). Squares 10 mm, pitch
14 mm, fill lines 0.1 mm apart, bidirectional, 8 mm overscan, M4 dynamic power. X runs towards
the left, Y towards the front: column 1 (30 %) is at the right, row 1 (1500 mm/min) at the back.
Stop with feed hold on the display or the gamepad (Circle).
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
POWERS = [30, 42, 54, 66, 78, 90]                   # percent
SPEEDS = [1500, 2250, 3000, 3750, 4500]             # mm/min
SIZE, PITCH, STEP, OVER = 10.0, 14.0, 0.1, 8.0
SMAX = 1000


def arg(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def build(x0, y0):
    g = ['G21 G90 G54 M4 S0']
    for r, f in enumerate(SPEEDS):
        for c, p in enumerate(POWERS):
            xa, ya = x0 + c * PITCH, y0 + r * PITCH
            s = p * SMAX // 100
            for i in range(int(round(SIZE / STEP)) + 1):
                y = ya + i * STEP
                a, b = (xa, xa + SIZE) if i % 2 == 0 else (xa + SIZE, xa)
                d = 1 if b > a else -1
                g.append('G0 X%.3f Y%.3f' % (a - d * OVER, y))
                g.append('G1 X%.3f S0 F%d' % (a, f))
                g.append('G1 X%.3f S%d' % (b, s))
                g.append('G1 X%.3f S0' % (b + d * OVER))
    g += ['M5', 'G0 X%.3f Y%.3f' % (x0, y0)]
    return g


def run(lines):
    import serial, serial.tools.list_ports
    port = next((p.device for p in serial.tools.list_ports.comports() if p.vid == 0x0483 and p.pid == 0x5740), None)
    if not port:
        sys.exit('Board not found on USB.')
    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(0.3)
    ser.reset_input_buffer()
    for l in lines:
        ser.write((l + '\n').encode())
        while True:
            r = ser.readline().decode(errors='replace').strip()
            if r == 'ok':
                break
            if r.startswith('error') or r.startswith('ALARM'):
                ser.write(b'M5\n')
                sys.exit('%s -> %s (homed? limits?)' % (l, r))
    while True:
        ser.reset_input_buffer()
        ser.write(b'?')
        s = ser.readline().decode(errors='replace').strip()
        if s.startswith('<Idle') or s.startswith('<Alarm'):
            break
        time.sleep(0.5)
    print('done:', s)
    ser.dtr = False


def frame(x0, y0):
    x1, y1 = x0 + 5 * PITCH + SIZE, y0 + 4 * PITCH + SIZE
    return ['G21 G90 G54 M5 S0', 'G0 X%g Y%g' % (x0, y0)] + [
        'G1 X%g Y%g F3000' % p for p in ((x1, y0), (x1, y1), (x0, y1), (x0, y0))]


if __name__ == '__main__':
    x0, y0 = arg('--x', 40.0), arg('--y', 40.0)
    if '--frame' in sys.argv:                       # laser off, trace the outline only
        run(frame(x0, y0))
        sys.exit()
    lines = build(x0, y0)
    with open(os.path.join(HERE, 'laser_test.nc'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    mins = sum(6 * (SIZE / STEP + 1) * (SIZE + 2 * OVER) / f for f in SPEEDS)
    print('%d lines, about %.0f min; X %g..%g, Y %g..%g' % (
        len(lines), mins, x0, x0 + 5 * PITCH + SIZE, y0, y0 + 4 * PITCH + SIZE))
    if '--run' in sys.argv:
        run(lines)
