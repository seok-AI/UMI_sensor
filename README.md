# UMI Sensor Runtime: AnySkin + CoinFT

팀원이 새 Ubuntu PC/NUC에서 **AnySkin과 CoinFT를 연결 → 환경 설치 → 장치 확인 → 값 읽기 → 시각화 → CSV 기록**까지 바로 할 수 있도록 정리한 배포본입니다.

이 배포본에서 확인한 구성은 다음과 같습니다.

```text
AnySkin
AnySkin magnetometer board -> Adafruit QT Py -> USB -> /dev/ttyACM*

CoinFT (single)
CoinFT -> FT232R -> USB -> /dev/ttyUSB0

CoinFT (dual)
Left  CoinFT -> FT232R #1 -> USB -> NUC
Right CoinFT -> FT232R #2 -> USB -> NUC
```

> **중요:** CoinFT 두 개를 하나의 FT232/UART RX에 합치지 마세요. 직접 UART 패킷에는 sensor ID가 없으며, 두 송신 스트림이 충돌하면 주기적인 spike가 발생할 수 있습니다. 실제 셋업에서도 두 센서를 분리한 뒤 single-sensor spike가 사라졌습니다.

---

## 1. Repository structure

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
│       ├── CFT24_MLP.onnx
│       └── CFT24_norm.json
├── scripts/
│   └── check_devices.sh
├── docs/
│   ├── PROTOCOL_AND_DATA.md
│   └── TROUBLESHOOTING.md
└── licenses/
    ├── COINFT_LICENSE.txt
    └── THIRD_PARTY_NOTICES.md
```

`.venv`, Conda environment, upstream nested `.git`, calibration training datasets 등은 배포본에서 제외했습니다. GitHub에 그대로 올려도 됩니다.

---

# 2. Environment setup

## Recommended: one Conda environment for both sensors

Python 3.10 기준입니다.

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd UMI_sensor_release

conda env create -f environment.yml
conda activate umi-sensor
```

설치 확인:

```bash
python scripts/smoke_test.py
```

설치되는 핵심 패키지:

- `anyskin==1.0.0`
- `pyserial==3.5`
- `onnxruntime`
- `numpy`
- `matplotlib`

Conda를 사용하지 않는 경우 Python 3.10 환경에서:

```bash
pip install -r requirements.txt
```

AnySkin 공식 패키지의 stable release는 v1.0.0이며 `pip install anyskin` 및 `anyskin_viz <port>` 사용법을 제공합니다.

Official AnySkin: https://github.com/raunaqbhirangi/anyskin

Official CoinFT: https://github.com/coin-ft/coin-ft

---

# 3. Serial permission setup (Ubuntu)

먼저 현재 계정이 serial device를 열 수 있도록 `dialout` 그룹에 추가하는 것을 권장합니다.

```bash
sudo usermod -aG dialout $USER
```

그 후 **로그아웃 → 다시 로그인**합니다.

확인:

```bash
groups
```

급하게 일회성 테스트만 할 때는:

```bash
sudo chmod a+rw /dev/ttyACM0
sudo chmod a+rw /dev/ttyUSB0
sudo chmod a+rw /dev/ttyUSB1
```

영구적인 운영에서는 `dialout` 방식을 권장합니다.

---

# 4. Check connected devices

센서를 USB에 연결한 뒤:

```bash
bash scripts/check_devices.sh
```

또는 직접:

```bash
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
ls -l /dev/serial/by-id/ 2>/dev/null
```

보통:

```text
AnySkin -> /dev/ttyACM0
CoinFT  -> /dev/ttyUSB0
```

CoinFT 두 개를 동시에 연결하면:

```text
/dev/ttyUSB0
/dev/ttyUSB1
```

이 됩니다. 단, `ttyUSB0/1` 번호는 재연결 또는 재부팅 시 바뀔 수 있으므로 dual 운용에서는 `/dev/serial/by-id/...` 사용을 권장합니다.

---

# 5. AnySkin

## 5.1 Hardware connection

AnySkin startup kit 기준:

```text
magnetometer board -> QWIIC -> Adafruit QT Py -> USB-C -> PC
```

USB 케이블은 **data 통신 가능한 케이블**이어야 합니다. 전원만 들어오고 `/dev/ttyACM*`가 생기지 않으면 케이블부터 교체해 보세요.

장치 확인:

```bash
ls /dev/ | grep -E 'ACM|USB'
```

## 5.2 Official visualization (recommended)

```bash
anyskin_viz /dev/ttyACM0
```

- tactile 반응이 실시간으로 표시됩니다.
- 시간이 지나 zero가 drift하면 **`B`** 키로 baseline을 다시 잡습니다.

## 5.3 Read raw AnySkin values in Python

```bash
python anyskin/read_anyskin.py --port /dev/ttyACM0
```

샘플 하나는:

```text
5 magnetometers x 3 axes = 15 values
```

입니다.

예시 형태:

```text
[[m0_x m0_y m0_z]
 [m1_x m1_y m1_z]
 ...
 [m4_x m4_y m4_z]]
```

이 값은 **자기장 기반 tactile raw signal**이며 N 단위의 힘이나 압력값이 아닙니다.

Python 코드에서 핵심 부분은:

```python
from anyskin import AnySkinBase

sensor = AnySkinBase(num_mags=5, port="/dev/ttyACM0")
timestamp, sample = sensor.get_sample()   # sample: 15 values
sensor.close()
```

## 5.4 Record AnySkin CSV

무기한 기록:

```bash
python anyskin/record_anyskin_csv.py --port /dev/ttyACM0
```

10초 기록:

```bash
python anyskin/record_anyskin_csv.py \
  --port /dev/ttyACM0 \
  --duration 10
```

기본 저장 위치:

```text
recordings/anyskin_YYYYMMDD_HHMMSS.csv
```

---

# 6. CoinFT hardware rule — 가장 중요

## Single sensor

```text
CoinFT -> FT232R -> NUC
```

하나만 꽂으면 Left든 Right든 대부분 `/dev/ttyUSB0`로 보입니다. 따라서 하나씩 번갈아 검증할 때는 둘 다 `/dev/ttyUSB0`를 사용하면 됩니다.

## Dual sensor

반드시:

```text
Left  CoinFT -> FT232R #1 -> NUC
Right CoinFT -> FT232R #2 -> NUC
```

처럼 **센서별 독립 UART**를 사용합니다.

다음 구성은 사용하지 마세요:

```text
Left CoinFT  --\
               +--> one FT232R -> PC   X
Right CoinFT --/
```

이 구성에서는 패킷 충돌 때문에 여러 F/T 축이 동시에 튀는 periodic spike가 발생할 수 있습니다.

---

# 7. CoinFT: single sensor test

## 7.1 Raw values only

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode raw
```

CoinFT CFT24 direct packet은 이 셋업에서 12개의 raw uint16 channel을 제공합니다.

## 7.2 Tare-zeroed raw

센서를 건드리지 않은 상태에서 실행:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode zeroed
```

처음 500 sample을 이용해 raw baseline을 잡습니다.

## 7.3 Calibrated 6-axis F/T

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode wrench
```

출력:

```text
Fx, Fy, Fz : N
Mx, My, Mz : Nm
```

raw부터 모두 같이 보고 싶으면:

```bash
python coinft/read_coinft.py --port /dev/ttyUSB0 --mode all
```

---

# 8. CoinFT: single visualization

기본 XYZ 한 plot:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left
```

Z축 scale이 커서 X/Y가 잘 안 보이면 권장 옵션:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --split-z
```

`--split-z` 화면:

```text
Force XY  : Fx, Fy
Force Z   : Fz
Moment XY : Mx, My
Moment Z  : Mz
```

그래프 Y축은 초기 범위에서 시작하고, 값이 범위를 벗어날 때만 확장됩니다. 자동으로 다시 축소되지는 않습니다.

Matplotlib 창에서:

```text
r = Y-axis 초기 범위로 reset
```

---

# 9. CoinFT: dual sensor setup

두 FT232를 연결한 다음:

```bash
ls -l /dev/serial/by-id/
```

예시:

```text
usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0 -> ../../ttyUSB0
usb-FTDI_FT232R_USB_UART_B1234567-if00-port0 -> ../../ttyUSB1
```

어느 FT232가 Left/Right인지 한 번 확인한 뒤 serial ID를 기록해 두는 것을 권장합니다.

Dual visualization:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port /dev/ttyUSB0 \
  --right-port /dev/ttyUSB1 \
  --split-z
```

실제 장기 운용에서는:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port /dev/serial/by-id/<LEFT_FTDI_ID> \
  --right-port /dev/serial/by-id/<RIGHT_FTDI_ID> \
  --split-z
```

를 권장합니다.

Dual reader는 두 UART를 별도 background thread에서 읽습니다. 한 포트의 blocking read가 다른 포트의 데이터를 막지 않도록 구성했습니다.

---

# 10. CoinFT CSV recording

## Single

```bash
python coinft/record_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --duration 30
```

CSV에는 다음이 함께 저장됩니다.

```text
host_time
raw0 ... raw11
raw_zeroed0 ... raw_zeroed11
Fx_N Fy_N Fz_N Mx_Nm My_Nm Mz_Nm
```

## Dual

```bash
python coinft/record_coinft_dual.py \
  --left-port /dev/ttyUSB0 \
  --right-port /dev/ttyUSB1 \
  --duration 30
```

두 CoinFT는 서로 독립 UART/clock이므로, dual CSV는 억지로 한 row에 동기화하지 않고 **event-style**로 저장합니다.

```text
host_time, sensor, raw..., raw_zeroed..., wrench...
```

`sensor` column이 `Left` 또는 `Right`를 나타냅니다.

---

# 11. CoinFT data meaning

코드 내부 processing 순서:

```text
CoinFT
  -> 12-D raw uint16
  -> raw tare offset subtraction
  -> normalize using CFT24_norm.json
  -> CFT24_MLP.onnx
  -> 6-D calibrated wrench
  -> optional moving average for visualization only
```

즉 그래프에 보이는 값은 raw가 아니라:

```text
[Fx, Fy, Fz, Mx, My, Mz]
```

6축 F/T 추정값입니다.

자세한 내용: `docs/PROTOCOL_AND_DATA.md`

---

# 12. Calibration warning

현재 포함한:

```text
coinft/hardware_configs/CFT24_MLP.onnx
coinft/hardware_configs/CFT24_norm.json
```

은 초기 셋업에 사용한 upstream CoinFT calibration artifact입니다.

센서가 움직이는지 확인하고 상대적인 반응을 보는 데는 사용할 수 있지만, **다른 실제 CoinFT unit에서도 절대적인 N/Nm 값이 정확하다고 가정하면 안 됩니다.** 정량적인 force/torque 실험 전에 각 물리 센서와 calibration 파일이 맞는지 확인하세요.

Single script는 custom calibration을 받을 수 있습니다.

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --model path/to/model.onnx \
  --norm path/to/norm.json
```

Dual은 Left/Right calibration을 각각 지정할 수 있습니다.

```bash
python coinft/visualize_coinft_dual.py \
  --left-port /dev/ttyUSB0 \
  --right-port /dev/ttyUSB1 \
  --left-model path/to/left.onnx \
  --left-norm path/to/left.json \
  --right-model path/to/right.onnx \
  --right-norm path/to/right.json
```

---

# 13. Recommended bring-up sequence for a new PC

팀원이 처음 받을 때 아래 순서만 따르면 됩니다.

### A. Install

```bash
conda env create -f environment.yml
conda activate umi-sensor
sudo usermod -aG dialout $USER
# logout/login once
```

### B. AnySkin

```bash
bash scripts/check_devices.sh
anyskin_viz /dev/ttyACM0
python anyskin/read_anyskin.py --port /dev/ttyACM0
```

### C. CoinFT Left only

```bash
python coinft/read_coinft.py --port /dev/ttyUSB0 --mode raw
python coinft/visualize_coinft_single.py --port /dev/ttyUSB0 --label Left --split-z
```

### D. CoinFT Right only

Left FT232를 빼고 Right FT232만 꽂습니다. 하나만 꽂혀 있으면 보통 다시 `/dev/ttyUSB0`입니다.

```bash
python coinft/read_coinft.py --port /dev/ttyUSB0 --mode raw
python coinft/visualize_coinft_single.py --port /dev/ttyUSB0 --label Right --split-z
```

### E. Both CoinFTs

두 FT232를 동시에 꽂습니다.

```bash
ls -l /dev/serial/by-id/
python coinft/visualize_coinft_dual.py \
  --left-port <LEFT_PORT> \
  --right-port <RIGHT_PORT> \
  --split-z
```

### F. Record data

```bash
python anyskin/record_anyskin_csv.py --duration 30
python coinft/record_coinft_dual.py --left-port <LEFT_PORT> --right-port <RIGHT_PORT> --duration 30
```

---

# 14. Known pitfalls

- **USB cable:** AnySkin이 켜지지만 serial device가 안 보이면 charge-only cable 가능성 확인.
- **Permission denied:** `dialout` group 확인.
- **AnySkin drift:** official visualizer에서 `B`로 baseline recalibration.
- **CoinFT tare:** 시작할 때 센서를 누르거나 하중을 주지 말 것.
- **CoinFT dual wiring:** 반드시 FT232R 2개, UART 2개.
- **Port order:** dual에서 `/dev/ttyUSB0/1`은 고정 ID가 아님. `/dev/serial/by-id` 권장.
- **Periodic CoinFT spike:** 두 CoinFT를 하나의 UART에 합친 연결을 먼저 의심.
- **Calibration:** 포함된 CFT24 model이 모든 물리 센서의 정확한 절대 calibration을 보장하지 않음.
- **Visualization smoothing:** plot에는 10-sample moving average가 적용되지만 CSV/raw reader는 원본 sample을 보존.

더 자세한 문제 해결은 `docs/TROUBLESHOOTING.md` 참고.

GitHub에 실제 release하기 전에는 `docs/GITHUB_RELEASE_CHECKLIST.md`도 확인하세요.

---

# 15. License / upstream attribution

AnySkin은 upstream MIT package를 dependency로 설치합니다.

CoinFT 관련 runtime/model은 Stanford CoinFT 자료를 포함/수정하고 있으므로 upstream의 **CC BY-NC-SA 4.0** 조건을 반드시 확인하세요.

- CoinFT full license: `licenses/COINFT_LICENSE.txt`
- Notices: `licenses/THIRD_PARTY_NOTICES.md`

특히 upstream CoinFT README는 commercial use뿐 아니라 일부 sponsored research도 별도 Stanford license가 필요할 수 있다고 명시합니다. 공개 GitHub 배포나 외부 과제 사용 전에 팀에서 license 적용 여부를 확인하세요.
