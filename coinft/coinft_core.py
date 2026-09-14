#!/usr/bin/env python3
"""Shared direct-UART utilities for CoinFT + FT232R.

Protocol handling is adapted from the upstream Stanford CoinFT project
(https://github.com/coin-ft/coin-ft) and is distributed subject to the
CoinFT CC BY-NC-SA 4.0 terms included in this repository.

Validated direct protocol used by this bundle:
  baud: 1,000,000
  commands: i = idle/reset, q = query packet size, s = stream
  packet: 0x02 + N little-endian uint16 channels + 0x03

For the CFT24 setup in this repository, q reports 26 bytes total, i.e.
12 uint16 channels between the start and end bytes.
"""

from __future__ import annotations

import json
import os
import struct
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
import onnxruntime as ort
import serial


BAUD_RATE = 1_000_000
START_BYTE = 0x02
END_BYTE = 0x03
DEFAULT_TIMEOUT = 0.1


class CoinFTProtocolError(RuntimeError):
    pass


class CoinFTDevice:
    def __init__(self, port: str, baud: int = BAUD_RATE, timeout: float = DEFAULT_TIMEOUT):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        self.packet_size: Optional[int] = None
        self.num_channels: Optional[int] = None

    def open(self):
        if self.ser is not None and self.ser.is_open:
            return self
        self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        self._idle()
        self._query_layout()
        return self

    def _idle(self):
        assert self.ser is not None
        self.ser.write(b"i")
        time.sleep(0.2)
        self.ser.reset_input_buffer()

    def _query_layout(self):
        assert self.ser is not None
        self.ser.write(b"q")
        time.sleep(0.02)
        response = self.ser.read(1)
        if len(response) != 1:
            raise CoinFTProtocolError(
                "CoinFT did not answer packet-size query 'q'. "
                "Check port, wiring, permission, and 1,000,000 baud direct-UART connection."
            )
        packet_size = response[0]
        if packet_size < 4 or (packet_size - 2) % 2 != 0:
            raise CoinFTProtocolError(f"Unexpected CoinFT packet size: {packet_size}")
        self.packet_size = packet_size
        self.num_channels = (packet_size - 2) // 2

    def start_stream(self):
        if self.ser is None:
            self.open()
        assert self.ser is not None
        self.ser.reset_input_buffer()
        self.ser.write(b"s")
        time.sleep(0.05)
        return self

    def read_raw(self) -> Optional[np.ndarray]:
        if self.ser is None or not self.ser.is_open:
            raise RuntimeError("CoinFT serial port is not open")
        if self.packet_size is None or self.num_channels is None:
            raise RuntimeError("CoinFT packet layout is unknown")

        while True:
            first = self.ser.read(1)
            if not first:
                return None
            if first[0] == START_BYTE:
                break

        remaining = self.ser.read(self.packet_size - 1)
        if len(remaining) != self.packet_size - 1:
            return None
        if remaining[-1] != END_BYTE:
            return None

        payload = remaining[:-1]
        values = struct.unpack("<" + "H" * self.num_channels, payload)
        return np.asarray(values, dtype=np.float64)

    def tare(self, samples: int = 500, ignore_first: int = 10) -> np.ndarray:
        if samples <= ignore_first:
            raise ValueError("samples must be greater than ignore_first")
        buf = []
        while len(buf) < samples:
            raw = self.read_raw()
            if raw is not None:
                buf.append(raw)
        arr = np.asarray(buf, dtype=np.float64)
        return arr[ignore_first:].mean(axis=0)

    def close(self):
        if self.ser is None:
            return
        try:
            if self.ser.is_open:
                self.ser.write(b"i")
        except Exception:
            pass
        try:
            self.ser.close()
        finally:
            self.ser = None

    def __enter__(self):
        self.open()
        self.start_stream()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


@dataclass
class CoinFTCalibrator:
    model_path: str
    norm_path: str

    def __post_init__(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(self.model_path)
        if not os.path.exists(self.norm_path):
            raise FileNotFoundError(self.norm_path)

        self.session = ort.InferenceSession(self.model_path)
        self.input_name = self.session.get_inputs()[0].name

        with open(self.norm_path, "r") as f:
            d = json.load(f)
        self.mu_x = np.asarray(d["mu_x"], dtype=np.float32)
        self.sd_x = np.asarray(d["sd_x"], dtype=np.float32)
        self.mu_y = np.asarray(d["mu_y"], dtype=np.float32)
        self.sd_y = np.asarray(d["sd_y"], dtype=np.float32)

    def predict(self, raw: np.ndarray, raw_offset: np.ndarray) -> np.ndarray:
        raw_zeroed = np.asarray(raw, dtype=np.float64) - np.asarray(raw_offset, dtype=np.float64)
        if raw_zeroed.shape[0] != self.mu_x.shape[0]:
            raise ValueError(
                f"Calibration expects {self.mu_x.shape[0]} channels, got {raw_zeroed.shape[0]}"
            )
        x_norm = (raw_zeroed.astype(np.float32) - self.mu_x) / self.sd_x
        pred_norm = self.session.run(None, {self.input_name: x_norm.reshape(1, -1)})[0].flatten()
        return pred_norm * self.sd_y + self.mu_y


def default_config_paths():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardware_configs")
    return (
        os.path.join(base, "CFT24_MLP.onnx"),
        os.path.join(base, "CFT24_norm.json"),
    )
