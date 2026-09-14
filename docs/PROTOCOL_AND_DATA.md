# Protocol and data semantics

## AnySkin

The Python package exposes samples from five 3-axis magnetometers:

- 5 magnetometers × 3 axes = 15 values per sample.
- These values are magnetic tactile signals. They are **not calibrated force/pressure values**.
- The official `anyskin_viz` visualizer displays tactile changes relative to a baseline. Press `B` to recalibrate the baseline when drift accumulates.

Official project: https://github.com/raunaqbhirangi/anyskin

## CoinFT direct UART used in this repository

This repository uses **one FT232R per CoinFT** and talks to each CoinFT directly.

Observed/official direct protocol:

- Baud rate: `1,000,000`
- `i`: idle/reset
- `q`: query packet size
- `s`: start streaming
- Start byte: `0x02`
- End byte: `0x03`
- CFT24 packet in this setup: 26 bytes total = 1 start + 12×uint16 + 1 end
- Sensor payload uses little-endian uint16 values.

The direct packet does **not contain a left/right sensor ID**. Therefore two CoinFT TX streams must not be electrically merged onto one FT232/UART. Use one FT232R for each CoinFT.

## CoinFT value pipeline

The runtime scripts use:

1. `raw`: 12 direct uint16 sensor channels.
2. `raw_zeroed = raw - tare_offset`: baseline-subtracted raw values.
3. Normalize the 12-D zeroed input using `CFT24_norm.json`.
4. Run `CFT24_MLP.onnx`.
5. Denormalize the 6-D output.
6. Visualizers apply a 10-sample moving average only for display.

The 6-D calibrated output is:

- `Fx, Fy, Fz` in N
- `Mx, My, Mz` in Nm

The units follow the upstream CoinFT calibration collection code.

### Calibration warning

`coinft/hardware_configs/CFT24_MLP.onnx` and `CFT24_norm.json` are the calibration artifacts included with the CoinFT source bundle used during setup. They may not provide accurate absolute force/torque values for a different physical CoinFT unit.

For quantitative research measurements, verify that each physical sensor uses its own appropriate calibration model and normalization constants. The single and dual visualization scripts accept custom `--model/--norm` or per-side model/norm arguments.
