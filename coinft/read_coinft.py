#!/usr/bin/env python3
"""Print CoinFT raw, zeroed-raw, and/or calibrated 6-axis wrench values."""

import argparse
import time

import numpy as np

from coinft_core import CoinFTCalibrator, CoinFTDevice, default_config_paths


def parse_args():
    model, norm = default_config_paths()
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyUSB0")
    p.add_argument("--mode", choices=["raw", "zeroed", "wrench", "all"], default="all")
    p.add_argument("--count", type=int, default=0, help="Printed samples; 0 = continuous")
    p.add_argument("--print-every", type=int, default=20, help="Print every Nth received packet")
    p.add_argument("--tare-samples", type=int, default=500)
    p.add_argument("--model", default=model)
    p.add_argument("--norm", default=norm)
    return p.parse_args()


def fmt(arr, precision=4):
    return np.array2string(np.asarray(arr), precision=precision, suppress_small=False)


def main():
    args = parse_args()
    need_tare = args.mode in {"zeroed", "wrench", "all"}
    need_model = args.mode in {"wrench", "all"}

    cal = CoinFTCalibrator(args.model, args.norm) if need_model else None

    dev = CoinFTDevice(args.port)
    try:
        dev.open()
        print(f"Connected: {args.port}")
        print(f"Packet size: {dev.packet_size} bytes, channels: {dev.num_channels}")
        dev.start_stream()

        offset = None
        if need_tare:
            print(f"Taring raw channels with {args.tare_samples} samples. Do not touch the sensor...")
            offset = dev.tare(args.tare_samples)
            print("Tare complete.")

        received = 0
        printed = 0
        print("Ctrl+C to stop.\n")
        while args.count <= 0 or printed < args.count:
            raw = dev.read_raw()
            if raw is None:
                continue
            received += 1
            if received % max(args.print_every, 1) != 0:
                continue

            printed += 1
            print(f"sample={printed} host_time={time.time():.6f}")
            if args.mode in {"raw", "all"}:
                print("raw uint16-ish:", fmt(raw, 0))
            if args.mode in {"zeroed", "all"}:
                print("raw_zeroed    :", fmt(raw - offset, 2))
            if args.mode in {"wrench", "all"}:
                wrench = cal.predict(raw, offset)
                print(
                    "wrench         :",
                    f"Fx={wrench[0]: .4f} N, Fy={wrench[1]: .4f} N, Fz={wrench[2]: .4f} N, "
                    f"Mx={wrench[3]: .5f} Nm, My={wrench[4]: .5f} Nm, Mz={wrench[5]: .5f} Nm",
                )
            print()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        dev.close()


if __name__ == "__main__":
    main()
