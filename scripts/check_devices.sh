#!/usr/bin/env bash

set -u

echo "=== Serial device nodes ==="
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || echo "No /dev/ttyACM* or /dev/ttyUSB* devices found."

echo
echo "=== Stable serial IDs ==="
ls -l /dev/serial/by-id/ 2>/dev/null || echo "No /dev/serial/by-id entries found."

echo
echo "=== Relevant USB devices ==="
lsusb 2>/dev/null | grep -Ei 'FTDI|Adafruit|Teensy|Arduino' || echo "No matching USB device found in lsusb output."

echo
echo "=== User groups ==="
groups

echo
echo "Tip: the current user should usually belong to the 'dialout' group on Ubuntu."
