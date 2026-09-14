#!/usr/bin/env python3
"""Record raw AnySkin samples to CSV."""

import argparse
import csv
import os
import time
from datetime import datetime

import numpy as np
from anyskin import AnySkinBase


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--duration", type=float, default=0.0, help="Seconds; 0 = until Ctrl+C")
    p.add_argument("--output", default=None, help="Output CSV path")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs("recordings", exist_ok=True)
    output = args.output or os.path.join(
        "recordings", f"anyskin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    sensor = AnySkinBase(num_mags=5, port=args.port)
    header = ["host_time", "sensor_time"] + [
        f"mag{i}_{axis}" for i in range(5) for axis in ("x", "y", "z")
    ]

    start = time.time()
    count = 0
    try:
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            print(f"Recording AnySkin -> {output}")
            print("Ctrl+C to stop.")

            while args.duration <= 0 or time.time() - start < args.duration:
                sensor_time, sample = sensor.get_sample()
                host_time = time.time()
                values = np.asarray(sample).reshape(-1).tolist()
                writer.writerow([host_time, sensor_time, *values])
                count += 1
    except KeyboardInterrupt:
        pass
    finally:
        sensor.close()
        print(f"Saved {count} samples to {output}")


if __name__ == "__main__":
    main()
