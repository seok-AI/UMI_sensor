#!/usr/bin/env python3
"""Real-time visualization for one CoinFT connected through one FT232R."""

import argparse
import time
from collections import deque

import matplotlib.pyplot as plt
import numpy as np

from coinft_core import CoinFTCalibrator, CoinFTDevice, default_config_paths


PLOT_HISTORY = 5.0
WINDOW_SIZE = 10
PLOT_REFRESH_SEC = 0.04

FORCE_INIT = [-10.0, 10.0]
MOMENT_INIT = [-0.2, 0.2]
FORCE_XY_INIT = [-10.0, 10.0]
FORCE_Z_INIT = [-30.0, 30.0]
MOMENT_XY_INIT = [-0.2, 0.2]
MOMENT_Z_INIT = [-0.5, 0.5]
FORCE_MARGIN = 3.0
MOMENT_MARGIN = 0.1


def parse_args():
    model, norm = default_config_paths()
    p = argparse.ArgumentParser()
    p.add_argument("--port", default="/dev/ttyUSB0")
    p.add_argument("--label", default="CoinFT")
    p.add_argument("--split-z", action="store_true", help="Separate Z from X/Y due to scale difference")
    p.add_argument("--tare-samples", type=int, default=500)
    p.add_argument("--model", default=model)
    p.add_argument("--norm", default=norm)
    return p.parse_args()


def expand(lim, values, margin):
    lo, hi = lim
    if values:
        lo = min(lo, min(values) - margin if min(values) < lo else lo)
        hi = max(hi, max(values) + margin if max(values) > hi else hi)
    return [lo, hi]


def main():
    args = parse_args()
    cal = CoinFTCalibrator(args.model, args.norm)
    dev = CoinFTDevice(args.port)

    try:
        dev.open()
        print(f"Connected {args.label}: {args.port}; channels={dev.num_channels}")
        dev.start_stream()
        print(f"Taring with {args.tare_samples} samples. Do not touch the sensor...")
        offset = dev.tare(args.tare_samples)
        print("Tare complete.")

        plt.ion()
        if args.split_z:
            fig, axes = plt.subplots(4, 1, figsize=(9, 10), sharex=True)
            ax_fxy, ax_fz, ax_mxy, ax_mz = axes
            fxy = [ax_fxy.plot([], [], label="Fx")[0], ax_fxy.plot([], [], label="Fy")[0]]
            fz = ax_fz.plot([], [], label="Fz")[0]
            mxy = [ax_mxy.plot([], [], label="Mx")[0], ax_mxy.plot([], [], label="My")[0]]
            mz = ax_mz.plot([], [], label="Mz")[0]
            titles = [f"{args.label} - Force XY", f"{args.label} - Force Z", f"{args.label} - Moment XY", f"{args.label} - Moment Z"]
            ylabels = ["Force [N]", "Force [N]", "Moment [Nm]", "Moment [Nm]"]
            for ax, title, ylabel in zip(axes, titles, ylabels):
                ax.set_title(title); ax.set_ylabel(ylabel); ax.grid(True); ax.legend(loc="upper right")
            axes[-1].set_xlabel("Time [s]")
            limits = [FORCE_XY_INIT.copy(), FORCE_Z_INIT.copy(), MOMENT_XY_INIT.copy(), MOMENT_Z_INIT.copy()]
            for ax, lim in zip(axes, limits): ax.set_ylim(*lim)
        else:
            fig, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
            ax_f, ax_m = axes
            flines = [ax_f.plot([], [], label=x)[0] for x in ("Fx", "Fy", "Fz")]
            mlines = [ax_m.plot([], [], label=x)[0] for x in ("Mx", "My", "Mz")]
            ax_f.set_title(f"{args.label} - Force"); ax_m.set_title(f"{args.label} - Moment")
            ax_f.set_ylabel("Force [N]"); ax_m.set_ylabel("Moment [Nm]"); ax_m.set_xlabel("Time [s]")
            for ax in axes: ax.grid(True); ax.legend(loc="upper right")
            limits = [FORCE_INIT.copy(), MOMENT_INIT.copy()]
            ax_f.set_ylim(*limits[0]); ax_m.set_ylim(*limits[1])

        def reset(event):
            nonlocal limits
            if event.key != "r": return
            limits = ([FORCE_XY_INIT.copy(), FORCE_Z_INIT.copy(), MOMENT_XY_INIT.copy(), MOMENT_Z_INIT.copy()]
                      if args.split_z else [FORCE_INIT.copy(), MOMENT_INIT.copy()])
            for ax, lim in zip(np.atleast_1d(axes), limits): ax.set_ylim(*lim)
            fig.canvas.draw_idle()
            print("Y-axis reset.")

        fig.canvas.mpl_connect("key_press_event", reset)
        t, fdata, mdata = [], [[], [], []], [[], [], []]
        ma = deque(maxlen=WINDOW_SIZE)
        start = time.time(); last_plot = 0.0
        print("Visualization started. Press r to reset Y scale; Ctrl+C to stop.")

        while plt.fignum_exists(fig.number):
            raw = dev.read_raw()
            if raw is None: continue
            ma.append(cal.predict(raw, offset))
            ft = np.mean(ma, axis=0)
            now = time.time() - start
            t.append(now)
            for j in range(3):
                fdata[j].append(float(ft[j])); mdata[j].append(float(ft[j+3]))
            while t and t[-1] - t[0] > PLOT_HISTORY:
                t.pop(0)
                for j in range(3): fdata[j].pop(0); mdata[j].pop(0)
            if time.time() - last_plot < PLOT_REFRESH_SEC: continue
            last_plot = time.time()
            xmin, xmax = max(0.0, t[-1]-PLOT_HISTORY), max(PLOT_HISTORY, t[-1])

            if args.split_z:
                for j in range(2): fxy[j].set_data(t, fdata[j]); mxy[j].set_data(t, mdata[j])
                fz.set_data(t, fdata[2]); mz.set_data(t, mdata[2])
                limits[0] = expand(limits[0], fdata[0]+fdata[1], FORCE_MARGIN)
                limits[1] = expand(limits[1], fdata[2], FORCE_MARGIN)
                limits[2] = expand(limits[2], mdata[0]+mdata[1], MOMENT_MARGIN)
                limits[3] = expand(limits[3], mdata[2], MOMENT_MARGIN)
                for ax, lim in zip(axes, limits): ax.set_ylim(*lim); ax.set_xlim(xmin, xmax)
            else:
                for j in range(3): flines[j].set_data(t, fdata[j]); mlines[j].set_data(t, mdata[j])
                limits[0] = expand(limits[0], fdata[0]+fdata[1]+fdata[2], FORCE_MARGIN)
                limits[1] = expand(limits[1], mdata[0]+mdata[1]+mdata[2], MOMENT_MARGIN)
                ax_f.set_ylim(*limits[0]); ax_m.set_ylim(*limits[1]); ax_f.set_xlim(xmin,xmax); ax_m.set_xlim(xmin,xmax)
            plt.pause(0.001)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        dev.close(); plt.close("all")


if __name__ == "__main__":
    main()
