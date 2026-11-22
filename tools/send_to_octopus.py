#!/usr/bin/env python3
"""
send_to_octopus.py - Explorer "Send to" target: copy G-code files to the SD card in the Octopus Pro

  python tools/send_to_octopus.py file1.nc [file2.nc ...]

Each file keeps its name on the card, an existing file of the same name is overwritten. Uses the YModem
upload of upload_firmware.py, also in alarm state (nothing moves, only the SD card is written).
The window closes 3 s after success and stays open after an error.
"""

import os
import sys
import time

import upload_firmware as uf

GCODE = ('.nc', '.gcode', '.ngc', '.tap')


def finish(ok):
    if ok:
        print('\nDone, the window closes in 3 s.')
        time.sleep(3)
    else:
        try:
            input('\nPress Enter to close.')
        except EOFError:
            pass
    sys.exit(0 if ok else 1)


def send(files):
    ser = uf.open_port()
    try:
        time.sleep(0.3)
        st = uf.status(ser)
        if not st.startswith(('<Idle', '<Alarm')):
            sys.exit(f'Machine is not idle ({st or "no status"}), nothing sent.')
        if not any(l == 'ok' for l in uf.command(ser, '$G', 2)):
            sys.exit('The board does not accept commands over USB, another stream is active '
                     '(a sender connected over WiFi?). Nothing sent.')
        uf.command(ser, '$FM', 5)   # mount the SD card
        for f in files:
            uf.TARGET = os.path.basename(f).lower()
            uf.upload(ser, f)
    finally:
        uf.close_port(ser)


def main():
    files = [f for f in sys.argv[1:] if os.path.isfile(f)]
    if not files:
        print('No file given. Use it from the Explorer: right click > Send to > Octopus SD.')
        finish(False)

    other = [f for f in files if not f.lower().endswith(GCODE)]
    if other:
        print('Not a G-code file (%s):' % ', '.join(GCODE))
        for f in other:
            print('  ' + f)
        if input('Send anyway? [y/N] ').strip().lower() not in ('y', 'j', 'yes', 'ja'):
            files = [f for f in files if f not in other]
            if not files:
                finish(False)

    try:
        send(files)
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f'\nError: {e.code}')
            finish(False)
    except Exception as e:
        print(f'\nError: {e}')
        finish(False)
    print(f'\n{len(files)} file(s) on the Octopus SD card.')
    finish(True)


if __name__ == '__main__':
    main()
