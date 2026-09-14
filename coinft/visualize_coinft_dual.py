#!/usr/bin/env python3
"""Real-time visualization for two CoinFTs, each on its own FT232R/UART."""

import argparse
import threading
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
    p.add_argument("--left-port", default="/dev/ttyUSB0")
    p.add_argument("--right-port", default="/dev/ttyUSB1")
    p.add_argument("--split-z", action="store_true")
    p.add_argument("--tare-samples", type=int, default=500)
    p.add_argument("--left-model", default=model); p.add_argument("--left-norm", default=norm)
    p.add_argument("--right-model", default=model); p.add_argument("--right-norm", default=norm)
    return p.parse_args()


def expand(lim, values, margin):
    lo, hi = lim
    if values:
        vmin, vmax = min(values), max(values)
        if vmin < lo: lo = vmin - margin
        if vmax > hi: hi = vmax + margin
    return [lo, hi]


class Reader:
    def __init__(self, name, port):
        self.name = name; self.dev = CoinFTDevice(port)
        self.latest = None; self.counter = 0; self.lock = threading.Lock(); self.running = False; self.thread = None
        self.tare_samples = []; self.collect_tare = False

    def start(self):
        self.dev.open(); self.dev.start_stream(); self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True); self.thread.start()

    def loop(self):
        while self.running:
            raw = self.dev.read_raw()
            if raw is None: continue
            with self.lock:
                self.latest = raw.copy(); self.counter += 1
                if self.collect_tare: self.tare_samples.append(raw.copy())

    def tare(self, n, ignore=10):
        with self.lock: self.tare_samples = []; self.collect_tare = True
        while True:
            with self.lock: count = len(self.tare_samples)
            if count >= n: break
            time.sleep(0.002)
        with self.lock:
            self.collect_tare = False; arr = np.asarray(self.tare_samples[:n])
        return arr[ignore:].mean(axis=0)

    def get(self):
        with self.lock:
            return (None if self.latest is None else self.latest.copy(), self.counter)

    def close(self):
        self.running = False
        if self.thread is not None: self.thread.join(timeout=1.0)
        self.dev.close()


def main():
    args = parse_args()
    if args.left_port == args.right_port: raise ValueError("Left and Right ports must be different")
    readers = [Reader("Left", args.left_port), Reader("Right", args.right_port)]
    cals = [CoinFTCalibrator(args.left_model, args.left_norm), CoinFTCalibrator(args.right_model, args.right_norm)]
    labels = ["Left Sensor", "Right Sensor"]

    try:
        for r in readers: r.start()
        print(f"Left: {args.left_port} (channels={readers[0].dev.num_channels})")
        print(f"Right: {args.right_port} (channels={readers[1].dev.num_channels})")
        print(f"Taring both sensors with {args.tare_samples} samples. Do not touch them...")
        offsets = [readers[0].tare(args.tare_samples), readers[1].tare(args.tare_samples)]
        print("Tare complete.")

        plt.ion()
        if args.split_z:
            fig, axes = plt.subplots(4, 2, figsize=(13, 11), sharex="col")
            lines=[]; limits=[]
            for i in range(2):
                fxy=[axes[0][i].plot([],[],label="Fx")[0],axes[0][i].plot([],[],label="Fy")[0]]
                fz=axes[1][i].plot([],[],label="Fz")[0]
                mxy=[axes[2][i].plot([],[],label="Mx")[0],axes[2][i].plot([],[],label="My")[0]]
                mz=axes[3][i].plot([],[],label="Mz")[0]
                lines.append(dict(fxy=fxy,fz=fz,mxy=mxy,mz=mz))
                titles=["Force XY","Force Z","Moment XY","Moment Z"]
                units=["Force [N]","Force [N]","Moment [Nm]","Moment [Nm]"]
                for row in range(4):
                    ax=axes[row][i]; ax.set_title(f"{labels[i]} - {titles[row]}"); ax.set_ylabel(units[row]); ax.grid(True); ax.legend(loc="upper right")
                axes[3][i].set_xlabel("Time [s]")
                lims=[FORCE_XY_INIT.copy(),FORCE_Z_INIT.copy(),MOMENT_XY_INIT.copy(),MOMENT_Z_INIT.copy()]
                limits.append(lims)
                for row in range(4): axes[row][i].set_ylim(*lims[row])
        else:
            fig, axes=plt.subplots(2,2,figsize=(12,8),sharex="col")
            lines=[]; limits=[]
            for i in range(2):
                fl=[axes[0][i].plot([],[],label=x)[0] for x in ("Fx","Fy","Fz")]
                ml=[axes[1][i].plot([],[],label=x)[0] for x in ("Mx","My","Mz")]
                lines.append(dict(force=fl,moment=ml)); limits.append([FORCE_INIT.copy(),MOMENT_INIT.copy()])
                axes[0][i].set_title(f"{labels[i]} - Force"); axes[1][i].set_title(f"{labels[i]} - Moment")
                axes[0][i].set_ylabel("Force [N]"); axes[1][i].set_ylabel("Moment [Nm]"); axes[1][i].set_xlabel("Time [s]")
                for row in range(2): axes[row][i].grid(True); axes[row][i].legend(loc="upper right"); axes[row][i].set_ylim(*limits[i][row])

        def reset(event):
            if event.key != "r": return
            for i in range(2):
                limits[i] = ([FORCE_XY_INIT.copy(),FORCE_Z_INIT.copy(),MOMENT_XY_INIT.copy(),MOMENT_Z_INIT.copy()] if args.split_z else [FORCE_INIT.copy(),MOMENT_INIT.copy()])
                for row, lim in enumerate(limits[i]): axes[row][i].set_ylim(*lim)
            fig.canvas.draw_idle(); print("Y-axis reset.")
        fig.canvas.mpl_connect("key_press_event", reset)

        data=[dict(t=[],f=[[],[],[]],m=[[],[],[]]) for _ in range(2)]
        ma=[deque(maxlen=WINDOW_SIZE),deque(maxlen=WINDOW_SIZE)]; last_counter=[-1,-1]
        start=time.time(); last_plot=0.0
        print("Visualization started. Press r to reset Y scale; Ctrl+C to stop.")

        while plt.fignum_exists(fig.number):
            now=time.time()-start
            for i in range(2):
                raw,c=readers[i].get()
                if raw is None or c==last_counter[i]: continue
                last_counter[i]=c; ma[i].append(cals[i].predict(raw,offsets[i])); ft=np.mean(ma[i],axis=0)
                d=data[i]; d['t'].append(now)
                for j in range(3): d['f'][j].append(float(ft[j])); d['m'][j].append(float(ft[j+3]))
                while d['t'] and d['t'][-1]-d['t'][0]>PLOT_HISTORY:
                    d['t'].pop(0)
                    for j in range(3): d['f'][j].pop(0); d['m'][j].pop(0)
            if time.time()-last_plot<PLOT_REFRESH_SEC: time.sleep(0.001); continue
            last_plot=time.time()
            for i in range(2):
                d=data[i]
                if not d['t']: continue
                xmin,xmax=max(0.0,d['t'][-1]-PLOT_HISTORY),max(PLOT_HISTORY,d['t'][-1])
                if args.split_z:
                    for j in range(2): lines[i]['fxy'][j].set_data(d['t'],d['f'][j]); lines[i]['mxy'][j].set_data(d['t'],d['m'][j])
                    lines[i]['fz'].set_data(d['t'],d['f'][2]); lines[i]['mz'].set_data(d['t'],d['m'][2])
                    limits[i][0]=expand(limits[i][0],d['f'][0]+d['f'][1],FORCE_MARGIN); limits[i][1]=expand(limits[i][1],d['f'][2],FORCE_MARGIN)
                    limits[i][2]=expand(limits[i][2],d['m'][0]+d['m'][1],MOMENT_MARGIN); limits[i][3]=expand(limits[i][3],d['m'][2],MOMENT_MARGIN)
                    for row in range(4): axes[row][i].set_ylim(*limits[i][row]); axes[row][i].set_xlim(xmin,xmax)
                else:
                    for j in range(3): lines[i]['force'][j].set_data(d['t'],d['f'][j]); lines[i]['moment'][j].set_data(d['t'],d['m'][j])
                    limits[i][0]=expand(limits[i][0],d['f'][0]+d['f'][1]+d['f'][2],FORCE_MARGIN); limits[i][1]=expand(limits[i][1],d['m'][0]+d['m'][1]+d['m'][2],MOMENT_MARGIN)
                    for row in range(2): axes[row][i].set_ylim(*limits[i][row]); axes[row][i].set_xlim(xmin,xmax)
            plt.pause(0.001)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        for r in readers:
            try: r.close()
            except Exception as e: print(f"close warning: {e}")
        plt.close("all")


if __name__ == "__main__":
    main()
