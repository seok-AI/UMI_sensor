#!/usr/bin/env python3
"""Read raw AnySkin magnetic tactile data from one sensor.

The AnySkin startup kit exposes five 3-axis magnetometers, so each sample has
15 values. These are magnetic/tactile signals, not calibrated force values.
"""

import argparse
import time

import numpy as np
from anyskin import AnySkinBase


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyACM0", help="AnySkin serial port")
    p.add_argument("--count", type=int, default=0, help="Number of samples; 0 = continuous")
    p.add_argument("--print-every", type=int, default=1, help="Print every Nth sample")
    return p.parse_args()


def main():
    args = parse_args()
    sensor = AnySkinBase(num_mags=5, port=args.port)

    print(f"AnySkin connected: {args.port}")
    print("Sample shape: 5 magnetometers x 3 axes = 15 values")
    print("Ctrl+C to stop.\n")

    n = 0
    try:
        while args.count <= 0 or n < args.count:
            timestamp, sample = sensor.get_sample()
            n += 1
            if n % max(args.print_every, 1) != 0:
                continue

            data = np.asarray(sample).reshape(5, 3)
            print(f"sample={n} time={timestamp:.6f}")
            print(data)
            print()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sensor.close()


if __name__ == "__main__":
    main()
