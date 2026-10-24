#!/usr/bin/env python3
"""
motor_test.py - find the max feed rate and acceleration of an axis by ear

Sets $11x (max rate, mm/min) and $12x (acceleration, mm/s2) of one axis, moves it back and forth
between two machine positions and returns to the first one. Listen for stalls, rattling or a
changed sound. The values stay set (they are stored in the controller): restore them with --restore.

  python tools/motor_test.py X 6000 160 40 240 3     axis, rate, accel, from, to, cycles
  python tools/motor_test.py X 6000 160 40 240 3 --home   home ($H) first
  python tools/motor_test.py X 6000 160 40 240 3 --home --check   afterwards move slowly onto the
                                                    homing switch: its position shows lost steps
  python tools/motor_test.py --check-only X         reference: home, then the switch position
  python tools/motor_test.py --check-now X          switch position of one axis without homing first
  python tools/motor_test.py --all 10 home          all axes at once with the stored settings, then
                                                    the switch positions of X, Y and Z
  python tools/motor_test.py --restore              set the values saved on the first run again

Positions are machine coordinates (G53). The machine must be homed and idle, no program may
have the USB port open. Soft limits ($20) stay on. Requires pyserial.
"""

import json
import os
import sys
import time

import serial
import serial.tools.list_ports

USB_VID, USB_PID = 0x0483, 0x5740
AXES = {'X': 0, 'Y': 1, 'Z': 2}
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'motor_test_saved.json')


def open_port():
    for p in serial.tools.list_ports.comports():
        if p.vid == USB_VID and p.pid == USB_PID:
            return serial.Serial(p.device, 115200, timeout=0.5)
    sys.exit('Board not found on USB.')


def command(ser, cmd, timeout=5.0):
    ser.reset_input_buffer()
    ser.write((cmd + '\n').encode())
    end = time.time() + timeout
    lines = []
    while time.time() < end:
        line = ser.readline().decode(errors='replace').strip()
        if line:
            lines.append(line)
            if line == 'ok' or line.startswith('error') or line.startswith('ALARM'):
                break
    return lines


def status(ser):
    ser.reset_input_buffer()
    ser.write(b'?')
    end = time.time() + 2
    while time.time() < end:
        line = ser.readline().decode(errors='replace').strip()
        if line.startswith('<'):
            return line
    return ''


def setting(ser, n):
    for line in command(ser, '$' + str(n)):
        if line.startswith('$%d=' % n):
            return line.split('=', 1)[1]
    return None


def wait_idle(ser, timeout=300):
    end = time.time() + timeout
    while time.time() < end:
        s = status(ser)
        if s.startswith('<Idle'):
            return s
        if s.startswith('<Alarm') or s.startswith('<Hold'):
            return s
        time.sleep(0.2)
    return 'timeout'


def check_switch(ser, axis):
    """Move slowly onto the homing switch (side from $23) and return the machine position where it
    triggers: compared with the value right after homing it shows lost steps. The hard limit alarm
    is reset and the machine homed again afterwards."""
    i = AXES[axis]
    d = -1 if int(float(setting(ser, 23))) & (1 << i) else 1   # $23: homing direction inverted = switch at the minimum
    soft = setting(ser, 20)
    command(ser, '$20=0')                               # the switch is just outside the soft limits
    command(ser, 'G53 G0 %s%g' % (axis, -5 * d))
    wait_idle(ser)
    r = command(ser, 'G53 G1 %s%g F30' % (axis, 10 * d))   # not $J: jogging stays inside the limits ($40)
    if r[-1:] != ['ok']:
        print('move refused:', r)
    pos = None
    moving = False
    end = time.time() + 60
    while time.time() < end:
        s = status(ser)
        if s.startswith('<Alarm'):
            pos = float(s.split('MPos:')[1].split('|')[0].split(',')[i])
            break
        if s.startswith('<Run'):
            moving = True
        elif s.startswith('<Idle') and moving:
            break                                       # reached -10 without the switch
        time.sleep(0.05)
    ser.write(b'\x18')                                  # reset the hard limit alarm
    time.sleep(1.5)
    ser.reset_input_buffer()
    command(ser, '$20=%s' % soft)
    for attempt in range(2):        # a ganged axis still on one of its switches fails the first homing (alarm 8)
        r = command(ser, '$H', 120)
        if r[-1:] == ['ok']:
            break
        ser.write(b'\x18')
        time.sleep(1.5)
        ser.reset_input_buffer()
    else:
        print('homing after the check failed:', r)
    return pos


def main():
    ser = open_port()
    time.sleep(0.3)

    if len(sys.argv) == 2 and sys.argv[1] == '--restore':
        if not os.path.exists(SAVE):
            sys.exit('Nothing saved.')
        saved = json.load(open(SAVE))
        for n, v in saved.items():
            print('$%s=%s' % (n, v), command(ser, '$%s=%s' % (n, v))[-1:])
        os.remove(SAVE)
        ser.dtr = False
        return

    if len(sys.argv) == 3 and sys.argv[1] == '--check-only':
        axis = sys.argv[2].upper()
        r = command(ser, '$H', 120)
        print('homing:', r[-1:])
        print('%s switch triggers at %s' % (axis, check_switch(ser, axis)))
        ser.dtr = False
        return

    if len(sys.argv) == 3 and sys.argv[1] == '--check-now':
        # switch position right now, without homing first (after a job or a show). Only one axis:
        # the check ends in a limit alarm and homing.
        if not status(ser).startswith('<Idle'):
            sys.exit('Machine not idle')
        axis = sys.argv[2].upper()
        print('%s switch triggers at %s' % (axis, check_switch(ser, axis)))
        ser.dtr = False
        return

    if len(sys.argv) == 4 and sys.argv[1] == '--all':
        # all axes at once with the stored rates and accelerations: between two corner points
        p0, p1 = (40, 40, -10), (140, 140, -80)
        cycles = int(sys.argv[2])
        if sys.argv[3] == 'home':
            print('homing:', command(ser, '$H', 120)[-1:])
        g = lambda p: 'G53 G0 X%g Y%g Z%g' % p
        t0 = time.time()
        command(ser, g(p0))
        for _ in range(cycles):
            command(ser, g(p1))
            command(ser, g(p0))
        end = wait_idle(ser)
        print('XYZ %s <-> %s, %d cycles, done in %.1f s: %s' % (p0, p1, cycles, time.time() - t0, end))
        if end.startswith('<Idle'):
            for axis in 'XYZ':
                print('%s switch triggers at %s' % (axis, check_switch(ser, axis)))
        ser.dtr = False
        return

    home = '--home' in sys.argv     # home first, so no position error is carried over from a test before
    if home:
        sys.argv.remove('--home')
    check = '--check' in sys.argv   # afterwards: where does the homing switch trigger (lost steps)
    if check:
        sys.argv.remove('--check')

    if len(sys.argv) != 7 or sys.argv[1].upper() not in AXES:
        sys.exit(__doc__)

    if home:
        r = command(ser, '$H', 120)
        print('homing:', r[-1:])
        if r[-1:] != ['ok']:
            sys.exit('Homing failed')

    axis = sys.argv[1].upper()
    rate, accel, p0, p1, cycles = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6])
    i = AXES[axis]

    s = status(ser)
    if not s.startswith('<Idle'):
        sys.exit('Machine not idle: ' + s)

    # remember the original values once
    if not os.path.exists(SAVE):
        json.dump({str(n): setting(ser, n) for n in (110 + i, 120 + i)}, open(SAVE, 'w'))

    for n, v in ((110 + i, rate), (120 + i, accel)):
        r = command(ser, '$%d=%g' % (n, v))
        if r[-1:] != ['ok']:
            sys.exit('$%d=%g: %s' % (n, v, r))

    rpm = rate * float(setting(ser, 100 + i)) / (200 * float(setting(ser, 150 + i)))
    print('%s: %g mm/min (%.0f rpm), %g mm/s2, %g <-> %g, %d cycles' % (axis, rate, rpm, accel, p0, p1, cycles))

    t0 = time.time()
    command(ser, 'G53 G0 %s%g' % (axis, p0))
    for _ in range(cycles):
        command(ser, 'G53 G0 %s%g' % (axis, p1))
        command(ser, 'G53 G0 %s%g' % (axis, p0))
    end = wait_idle(ser)
    print('done in %.1f s: %s' % (time.time() - t0, end))
    if check and end.startswith('<Idle'):
        print('%s switch triggers at %s' % (axis, check_switch(ser, axis)))
    ser.dtr = False


if __name__ == '__main__':
    main()
