### Macro Keyboard

This project transforms every USB keyboard into a macro keyboard which can run arbitrary scripts on key press (and kill them on release). It uses evdev to grab a device specified by /dev/input/ path and uses KEYMAP to create a mapping KEY <> script. 

The keyboard is "grabbed" by evdev which prevents the keyboard from sending keys to the OS itself.

**Don't attach the script to your main keyboard. You won't be able to kill it aterwards.**