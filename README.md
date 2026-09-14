# UMI Sensor Runtime

Runtime tools for **AnySkin** tactile sensing and **CoinFT** force/torque sensing on Ubuntu/NUC systems.

Supported workflow:

```text
connect hardware -> set up environment -> verify serial device -> read data -> visualize -> record CSV
```

## Quick actions

### AnySkin

- [Visualize AnySkin](#visualize-anyskin)
- [Read raw AnySkin data](#read-anyskin-raw-data)
- [Record AnySkin data to CSV](#record-anyskin-data-to-csv)
- [Check AnySkin data format](#anyskin-data-format)
- [Troubleshoot AnySkin](#anyskin-troubleshooting)

### CoinFT

- [Read raw 12-channel data](#read-coinft-raw-data)
- [Read tare-zeroed raw data](#read-tare-zeroed-coinft-data)
- [Read 6-axis force/torque](#read-6-axis-force-and-torque)
- [Visualize one CoinFT](#visualize-one-coinft)
- [Visualize two CoinFTs](#visualize-two-coinfts)
- [Record one CoinFT to CSV](#record-one-coinft-to-csv)
- [Record two CoinFTs to CSV](#record-two-coinfts-to-csv)
- [Check CoinFT data format](#coinft-data-format)
- [Troubleshoot CoinFT](#coinft-troubleshooting)

### Setup

- [Install the environment](#install-the-environment)
- [Configure serial permissions](#configure-serial-permissions)
- [Find connected serial devices](#find-connected-serial-devices)
- [Run the recommended validation sequence](#recommended-validation-sequence)

---

## Setup

### Install the environment

Python 3.10 is recommended.

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd UMI_sensor_release

conda env create -f environment.yml
conda activate umi-sensor
```

Verify the installation:

```bash
python scripts/smoke_test.py
```

Without Conda:

```bash
pip install -r requirements.txt
```

Main dependencies:

- `anyskin==1.0.0`
- `pyserial==3.5`
- `onnxruntime`
- `numpy`
- `matplotlib`

### Configure serial permissions

Ubuntu serial devices are normally owned by the `dialout` group. Add the current user once:

```bash
sudo usermod -aG dialout $USER
```

Then **log out and log back in**, or reboot.

Verify:

```bash
groups
```

`dialout` should appear in the output.

Do not use `chmod` as a permanent fix. Commands such as:

```bash
sudo chmod a+rw /dev/ttyUSB0
```

only change the current device node. When the USB adapter is unplugged, that node is removed. Reconnecting the adapter creates a new node with the default permissions.

For a one-time test only:

```bash
sudo chmod a+rw /dev/ttyACM0
sudo chmod a+rw /dev/ttyUSB0
sudo chmod a+rw /dev/ttyUSB1
```

### Find connected serial devices

Use the helper script:

```bash
bash scripts/check_devices.sh
```

Or inspect devices directly:

```bash
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
ls -l /dev/serial/by-id/ 2>/dev/null
```

Typical mapping:

```text
AnySkin                    -> /dev/ttyACM0
One CoinFT + one FT232R    -> /dev/ttyUSB0
Two CoinFTs + two FT232Rs  -> /dev/ttyUSB0 and /dev/ttyUSB1
```

For two CoinFTs, prefer `/dev/serial/by-id/...` over `/dev/ttyUSB0` and `/dev/ttyUSB1`. The `ttyUSB` numbering may change after reconnecting or rebooting.

---

## AnySkin

### Hardware connection

Typical startup-kit connection:

```text
AnySkin magnetometer board -> QWIIC -> Adafruit QT Py -> USB -> PC
```

Use a USB cable that supports **data**, not a charge-only cable.

Confirm the device appears:

```bash
ls -l /dev/ttyACM* 2>/dev/null
```

### Visualize AnySkin

Use the official AnySkin visualizer:

```bash
anyskin_viz /dev/ttyACM0
```

The visualizer shows the response of the five magnetometers in real time.

Press `B` to reset the baseline if the zero point drifts.

### Read raw AnySkin data

```bash
python anyskin/read_anyskin.py \
  --port /dev/ttyACM0
```

Read a fixed number of samples:

```bash
python anyskin/read_anyskin.py \
  --port /dev/ttyACM0 \
  --count 100
```

Print every 10th sample:

```bash
python anyskin/read_anyskin.py \
  --port /dev/ttyACM0 \
  --print-every 10
```

### Record AnySkin data to CSV

Record until `Ctrl+C`:

```bash
python anyskin/record_anyskin_csv.py \
  --port /dev/ttyACM0
```

Record for 30 seconds:

```bash
python anyskin/record_anyskin_csv.py \
  --port /dev/ttyACM0 \
  --duration 30
```

Set the output path manually:

```bash
python anyskin/record_anyskin_csv.py \
  --port /dev/ttyACM0 \
  --duration 30 \
  --output recordings/anyskin_test.csv
```

### AnySkin data format

Each sample contains five 3-axis magnetometer measurements:

```text
5 magnetometers x 3 axes = 15 values
```

CSV columns:

```text
host_time
sensor_time
mag0_x mag0_y mag0_z
mag1_x mag1_y mag1_z
...
mag4_x mag4_y mag4_z
```

These are magnetic tactile signals. They are **not calibrated force values**.

### AnySkin troubleshooting

**No `/dev/ttyACM*` device**

- Check the USB cable first. A charge-only cable can power the board without exposing a serial device.
- Try another USB port.
- Run `dmesg | tail -50` immediately after reconnecting the device.

**Permission denied**

- Confirm the current user belongs to `dialout`.
- Log out and back in after changing group membership.

**Baseline drift**

- Press `B` in the official visualizer.

---

## CoinFT

### Hardware connection

A single CoinFT uses one FT232R adapter:

```text
CoinFT -> FT232R -> USB -> PC
```

Two CoinFTs require **two independent UART paths**:

```text
Left CoinFT  -> FT232R #1 -> USB -> PC
Right CoinFT -> FT232R #2 -> USB -> PC
```

Do **not** connect two CoinFT transmit streams to one FT232R/UART receive line. The native direct-UART packet does not contain a sensor ID. Combining two transmitters can cause packet collisions and periodic spikes.

When only one FT232R is connected, either the left or right sensor will normally appear as `/dev/ttyUSB0`.

### Read CoinFT raw data

Read the native 12-channel sensor values:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode raw
```

Print every received packet:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode raw \
  --print-every 1
```

### Read tare-zeroed CoinFT data

The first samples are used to estimate the raw baseline. Do not touch or load the sensor during tare.

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode zeroed
```

Default tare length: 500 samples.

To change it:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode zeroed \
  --tare-samples 1000
```

### Read 6-axis force and torque

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode wrench
```

Output:

```text
Fx, Fy, Fz  [N]
Mx, My, Mz  [Nm]
```

Show raw, zeroed raw, and wrench values together:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode all
```

### Visualize one CoinFT

Combined XYZ view:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left
```

Recommended view when Z has a much larger scale than X/Y:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --split-z
```

For a right sensor connected by itself:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Right \
  --split-z
```

Controls:

```text
r       reset plot Y-axis limits
Ctrl+C  stop
```

### Visualize two CoinFTs

Connect both FT232R adapters and check their IDs:

```bash
ls -l /dev/serial/by-id/
```

Use persistent FTDI paths when possible:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port /dev/serial/by-id/<LEFT_FTDI_ID> \
  --right-port /dev/serial/by-id/<RIGHT_FTDI_ID> \
  --split-z
```

For a quick test, `/dev/ttyUSB0` and `/dev/ttyUSB1` can also be used:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port /dev/ttyUSB0 \
  --right-port /dev/ttyUSB1 \
  --split-z
```

Verify which adapter is physically left and right before recording data.

### Record one CoinFT to CSV

```bash
python coinft/record_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --duration 30
```

Set the output path manually:

```bash
python coinft/record_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --duration 30 \
  --output recordings/coinft_left_test.csv
```

The CSV contains raw data, tare-zeroed raw data, and 6-axis wrench values.

### Record two CoinFTs to CSV

```bash
python coinft/record_coinft_dual.py \
  --left-port /dev/serial/by-id/<LEFT_FTDI_ID> \
  --right-port /dev/serial/by-id/<RIGHT_FTDI_ID> \
  --duration 30
```

The dual recorder writes an event-style CSV. Each row belongs to either the left or right sensor and carries its own host timestamp. The two FT232R/UART streams are independent and are not assumed to be perfectly synchronized.

### CoinFT data format

Direct UART settings used by this repository:

```text
baud rate: 1,000,000
frame:     0x02 + 12 x uint16 little-endian + 0x03
payload:   24 bytes
frame:     26 bytes total
```

Processing path:

```text
12-channel raw data
    -> tare subtraction
    -> input normalization
    -> CFT24_MLP.onnx
    -> output denormalization
    -> Fx Fy Fz Mx My Mz
```

Single-sensor CSV columns:

```text
host_time
label
raw0 ... raw11
raw_zeroed0 ... raw_zeroed11
Fx_N Fy_N Fz_N Mx_Nm My_Nm Mz_Nm
```

The visualization applies a moving average for readability. Raw readers and CSV recorders preserve native samples rather than saving the plotted smoothed signal.

### Calibration files

Default calibration files:

```text
coinft/hardware_configs/CFT24_MLP.onnx
coinft/hardware_configs/CFT24_norm.json
```

A single sensor can use custom calibration files:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --model path/to/model.onnx \
  --norm path/to/norm.json
```

Two sensors can use separate calibration files:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port <LEFT_PORT> \
  --right-port <RIGHT_PORT> \
  --left-model path/to/left.onnx \
  --left-norm path/to/left.json \
  --right-model path/to/right.onnx \
  --right-norm path/to/right.json
```

Do not assume that the included calibration model provides accurate absolute N/Nm values for every physical CoinFT unit. Verify the calibration before using the output for quantitative force/torque measurements.

### CoinFT troubleshooting

**Permission denied on `/dev/ttyUSB*`**

- Add the user to `dialout` and log out/in.
- Do not rely on repeated `chmod` after every reconnect.

**Periodic spikes while the sensor is untouched**

- Check the UART topology first.
- Each CoinFT should have its own FT232R/UART path.
- Two CoinFT transmit lines must not be merged into one FT232R receive line.

**Left and right sensors swap after reconnecting**

- `/dev/ttyUSB0` and `/dev/ttyUSB1` are not persistent identities.
- Use `/dev/serial/by-id/...` for dual operation.

**Large offset after startup**

- Start the program with the sensor unloaded.
- Do not touch either sensor during tare.
- Re-run the program if the initial tare was taken under load.

**Raw data is stable but wrench values are unexpected**

- Check the calibration model and normalization file.
- Inspect `--mode raw` before debugging the calibrated output.

---

## Recommended validation sequence

Run this sequence on a new machine or after rewiring the sensors.

### 1. Check the environment

```bash
conda activate umi-sensor
python scripts/smoke_test.py
```

### 2. Check serial devices

```bash
bash scripts/check_devices.sh
```

### 3. Test AnySkin

```bash
anyskin_viz /dev/ttyACM0
python anyskin/read_anyskin.py --port /dev/ttyACM0 --count 20
```

### 4. Test one CoinFT at a time

```bash
python coinft/read_coinft.py --port /dev/ttyUSB0 --mode raw --count 20 --print-every 1
python coinft/visualize_coinft_single.py --port /dev/ttyUSB0 --label Left --split-z
```

Disconnect that FT232R, connect the other one, and repeat with `--label Right`.

### 5. Test both CoinFTs

```bash
ls -l /dev/serial/by-id/
```

Then:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port <LEFT_PORT> \
  --right-port <RIGHT_PORT> \
  --split-z
```

Confirm:

- both columns update independently;
- pressing the left sensor primarily changes the left plots;
- pressing the right sensor primarily changes the right plots;
- no periodic spikes appear while both sensors are untouched.

### 6. Record a short dataset

```bash
python anyskin/record_anyskin_csv.py --duration 10
python coinft/record_coinft_dual.py \
  --left-port <LEFT_PORT> \
  --right-port <RIGHT_PORT> \
  --duration 10
```

Inspect the generated files in `recordings/` before starting a full data-collection session.

---

## Repository layout

```text
UMI_sensor_release/
├── README.md
├── environment.yml
├── requirements.txt
├── anyskin/
│   ├── read_anyskin.py
│   └── record_anyskin_csv.py
├── coinft/
│   ├── coinft_core.py
│   ├── read_coinft.py
│   ├── record_coinft_single.py
│   ├── record_coinft_dual.py
│   ├── visualize_coinft_single.py
│   ├── visualize_coinft_dual.py
│   └── hardware_configs/
├── scripts/
│   ├── check_devices.sh
│   └── smoke_test.py
├── docs/
│   ├── PROTOCOL_AND_DATA.md
│   ├── TROUBLESHOOTING.md
│   └── GITHUB_RELEASE_CHECKLIST.md
└── licenses/
```

Additional protocol and troubleshooting details are available in [`docs/`](docs/).

## Upstream projects and license

- AnySkin: https://github.com/raunaqbhirangi/anyskin
- CoinFT: https://github.com/coin-ft/coin-ft

See [`LICENSE`](LICENSE) and [`licenses/`](licenses/) before redistribution or use outside the intended research environment.
