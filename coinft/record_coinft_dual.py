#!/usr/bin/env python3
"""Record two CoinFT sensors on two FT232R adapters into one event-style CSV.

Each row records one native sample from one sensor. This avoids pretending that
the two independent UART clocks are perfectly synchronized.
"""

import argparse
import csv
import os
import queue
import threading
import time
from datetime import datetime

from coinft_core import CoinFTCalibrator, CoinFTDevice, default_config_paths


def parse_args():
    model, norm = default_config_paths()
    p=argparse.ArgumentParser()
    p.add_argument("--left-port",default="/dev/ttyUSB0"); p.add_argument("--right-port",default="/dev/ttyUSB1")
    p.add_argument("--duration",type=float,default=0.0); p.add_argument("--output",default=None); p.add_argument("--tare-samples",type=int,default=500)
    p.add_argument("--left-model",default=model); p.add_argument("--left-norm",default=norm); p.add_argument("--right-model",default=model); p.add_argument("--right-norm",default=norm)
    return p.parse_args()


def main():
    args=parse_args()
    if args.left_port==args.right_port: raise ValueError("Left and Right ports must be different")
    os.makedirs("recordings",exist_ok=True)
    output=args.output or os.path.join("recordings",f"coinft_dual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    devices=[CoinFTDevice(args.left_port),CoinFTDevice(args.right_port)]
    cals=[CoinFTCalibrator(args.left_model,args.left_norm),CoinFTCalibrator(args.right_model,args.right_norm)]
    labels=["Left","Right"]
    q=queue.Queue(maxsize=20000); stop=threading.Event(); threads=[]
    try:
        for d in devices: d.open(); d.start_stream()
        print(f"Taring both sensors with {args.tare_samples} samples. Do not touch them...")
        offsets=[devices[0].tare(args.tare_samples),devices[1].tare(args.tare_samples)]
        print("Tare complete.")
        n=devices[0].num_channels
        if devices[1].num_channels!=n: raise RuntimeError("Left/right channel counts differ")
        def worker(i):
            while not stop.is_set():
                raw=devices[i].read_raw()
                if raw is None: continue
                zeroed=raw-offsets[i]; wrench=cals[i].predict(raw,offsets[i])
                row=[time.time(),labels[i],*raw.tolist(),*zeroed.tolist(),*wrench.tolist()]
                try: q.put(row,timeout=0.1)
                except queue.Full: pass
        for i in range(2):
            t=threading.Thread(target=worker,args=(i,),daemon=True); t.start(); threads.append(t)
        header=["host_time","sensor"]+[f"raw{i}" for i in range(n)]+[f"raw_zeroed{i}" for i in range(n)]+["Fx_N","Fy_N","Fz_N","Mx_Nm","My_Nm","Mz_Nm"]
        start=time.time(); rows=0
        with open(output,"w",newline="") as f:
            w=csv.writer(f); w.writerow(header)
            print(f"Recording -> {output}"); print("Ctrl+C to stop.")
            while args.duration<=0 or time.time()-start<args.duration:
                try: row=q.get(timeout=0.2)
                except queue.Empty: continue
                w.writerow(row); rows+=1
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        for t in threads: t.join(timeout=1.0)
        for d in devices:
            try: d.close()
            except Exception: pass
        print(f"Saved dual CoinFT data to {output}")


if __name__=="__main__":
    main()
