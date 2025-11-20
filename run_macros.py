#!/usr/bin/env python3
import subprocess
from evdev import InputDevice, categorize, ecodes
from time import sleep

DEV_PATH = '/dev/input/by-id/usb-You_Streamdeck-event-kbd'  # or your /dev/input/eventX

# define what command/script to run per key
KEYMAP = {
    'KEY_COPY': ['/usr/bin/bash', '-c', 'xdotool click --repeat 10 --delay 18 1'],
    'KEY_F2': ['/usr/bin/bash', '-c', 'echo start F2; sleep 9999'],
}

# keep track of running processes by key name
running = {}

def main():
    dev = InputDevice(DEV_PATH)
    print(f"Opened {dev.path} ({dev.name})")
    dev.grab()  # prevent keyboard from typing in system

    try:
        for event in dev.read_loop():
            if event.type == ecodes.EV_KEY:
                keyevent = categorize(event)
                keyname = (
                    keyevent.keycode[0]
                    if isinstance(keyevent.keycode, (list, tuple))
                    else keyevent.keycode
                )
                if keyname not in KEYMAP:
                    print(f"Unknown key {keyname}")
                    continue  # skip unbound keys

                if keyevent.keystate == keyevent.key_down:
                    if keyname not in running:
                        proc = subprocess.Popen(KEYMAP[keyname])
                        running[keyname] = proc
                        print(f"[{keyname}] pressed → start script (pid: {proc.pid})")


                elif keyevent.keystate == keyevent.key_up:
                    proc = running.pop(keyname, None)
                    if proc:
                        print(f"[{keyname}] released → stop script (pid: {proc.pid})")
                        # send SIGTERM; change to SIGKILL if needed
                        proc.terminate()
    finally:
        dev.ungrab()

if __name__ == '__main__':
    main()