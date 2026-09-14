#!/usr/bin/env python3
"""Record one direct-UART CoinFT to CSV: raw, tare-zeroed raw, and 6-axis wrench."""

import argparse
import csv
import os
import time
from datetime import datetime

from coinft_core import CoinFTCalibrator, CoinFTDevice, default_config_paths


def parse_args():
    model, norm = default_config_paths()
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyUSB0")
    p.add_argument("--label", default="CoinFT")
    p.add_argument("--duration", type=float, default=0.0, help="Seconds; 0 = until Ctrl+C")
    p.add_argument("--output", default=None)
    p.add_argument("--tare-samples", type=int, default=500)
    p.add_argument("--model", default=model)
    p.add_argument("--norm", default=norm)
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs("recordings", exist_ok=True)
    output = args.output or os.path.join(
        "recordings", f"coinft_{args.label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    cal = CoinFTCalibrator(args.model, args.norm)
    dev = CoinFTDevice(args.port)
    rows = 0
    try:
        dev.open()
        dev.start_stream()
        print(f"Taring {args.label} with {args.tare_samples} samples. Do not touch the sensor...")
        offset = dev.tare(args.tare_samples)
        print("Tare complete.")

        n = dev.num_channels
        header = (
            ["host_time", "label"]
            + [f"raw{i}" for i in range(n)]
            + [f"raw_zeroed{i}" for i in range(n)]
            + ["Fx_N", "Fy_N", "Fz_N", "Mx_Nm", "My_Nm", "Mz_Nm"]
        )
        start = time.time()
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            print(f"Recording -> {output}")
            print("Ctrl+C to stop.")
            while args.duration <= 0 or time.time() - start < args.duration:
                raw = dev.read_raw()
                if raw is None:
                    continue
                zeroed = raw - offset
                wrench = cal.predict(raw, offset)
                writer.writerow([time.time(), args.label, *raw.tolist(), *zeroed.tolist(), *wrench.tolist()])
                rows += 1
    except KeyboardInterrupt:
        pass
    finally:
        dev.close()
        print(f"Saved {rows} rows to {output}")


if __name__ == "__main__":
    main()
