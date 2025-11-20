#!/usr/bin/env python3
import subprocess
import signal
import sys
from evdev import InputDevice, categorize, ecodes

DEV_PATH = '/dev/input/by-id/usb-You_Streamdeck-event-kbd' 

# define what command/script to run per key
KEYMAP = {
    'KEY_COPY': ['notify-send', 'hello world'],
    'KEY_F2': ['/usr/bin/bash', '-c', 'echo start F2; sleep 9999'],
}

# keep track of running processes by key name
running = {}

# reference stored so signal handler can access it
device = None


def stop_all_running():
    """Terminate all active child processes."""
    for key, proc in running.items():
        print(f"Stopping script for {key}")
        try:
            proc.terminate()
        except Exception as e:
            print(f"Error terminating {key}: {e}")
    running.clear()


def handle_sigint(sig, frame):
    """Gracefully handle Ctrl-C."""
    global device
    print("\nReceived Ctrl-C → cleaning up...")

    stop_all_running()

    if device:
        try:
            device.ungrab()
            print("Device ungrabbed.")
        except Exception:
            pass

    sys.exit(0)


# Register Ctrl-C handler
signal.signal(signal.SIGINT, handle_sigint)


def main():
    global device

    device = InputDevice(DEV_PATH)
    print(f"Opened {device.path} ({device.name})")

    # Grab keyboard to prevent system from seeing keypresses
    device.grab()

    try:
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                keyevent = categorize(event)
                keyname = (
                    keyevent.keycode[0]
                    if isinstance(keyevent.keycode, (list, tuple))
                    else keyevent.keycode
                )

                if keyname not in KEYMAP:
                    continue

                if keyevent.keystate == keyevent.key_down:
                    if keyname not in running:
                        print(f"[{keyname}] pressed → start script")
                        proc = subprocess.Popen(KEYMAP[keyname])
                        running[keyname] = proc

                elif keyevent.keystate == keyevent.key_up:
                    proc = running.pop(keyname, None)
                    if proc:
                        print(f"[{keyname}] released → stop script")
                        proc.terminate()

    finally:
        # Always try to ungrab even if loop ends unexpectedly
        try:
            device.ungrab()
            print("Device ungrabbed.")
        except Exception:
            pass

        stop_all_running()


if __name__ == '__main__':
    main()
