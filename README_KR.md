# UMI Sensor Runtime — 한국어 가이드

AnySkin 촉각 센서와 CoinFT 힘/토크 센서를 Ubuntu/NUC에서 연결하고, 값을 확인하고, 시각화하고, CSV로 저장하기 위한 사용 가이드입니다.

[English README](README.md)

---

## 바로가기

### AnySkin

- [AnySkin이 연결됐는지 확인하고 싶다](#anyskin-연결-확인)
- [AnySkin을 화면으로 보고 싶다](#anyskin-시각화)
- [AnySkin raw 값을 터미널에서 보고 싶다](#anyskin-raw-15d-읽기)
- [AnySkin 데이터를 CSV로 저장하고 싶다](#anyskin-csv-저장)
- [AnySkin 값이 어떤 데이터인지 알고 싶다](#anyskin-데이터-형식)
- [AnySkin이 안 될 때](#anyskin-문제-해결)

### CoinFT

- [CoinFT 하나가 연결됐는지 확인하고 싶다](#coinft-하나-연결-확인)
- [CoinFT raw 12채널 값을 보고 싶다](#coinft-raw-12채널-읽기)
- [초기값을 뺀 raw 값을 보고 싶다](#coinft-tare-zeroed-raw-읽기)
- [Fx, Fy, Fz, Mx, My, Mz 값을 보고 싶다](#coinft-6축-ft-읽기)
- [CoinFT 하나를 시각화하고 싶다](#coinft-하나-시각화)
- [CoinFT 두 개를 동시에 시각화하고 싶다](#coinft-두-개-동시-시각화)
- [CoinFT 하나를 CSV로 저장하고 싶다](#coinft-하나-csv-저장)
- [CoinFT 두 개를 CSV로 저장하고 싶다](#coinft-두-개-csv-저장)
- [CoinFT 값이 어떻게 만들어지는지 알고 싶다](#coinft-데이터-형식)
- [CoinFT가 안 되거나 값이 이상할 때](#coinft-문제-해결)

### 처음 설치할 때

- [환경 설치](#환경-설치)
- [USB serial 권한 설정](#usb-serial-권한-설정)
- [연결된 센서 포트 찾기](#연결된-센서-포트-찾기)
- [처음부터 순서대로 검증하기](#권장-검증-순서)

---

# 처음 설치할 때

## 환경 설치

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

Conda를 사용하지 않는 경우:

```bash
pip install -r requirements.txt
```

주요 패키지:

```text
anyskin==1.0.0
pyserial==3.5
onnxruntime
numpy
matplotlib
```

---

## USB serial 권한 설정

Ubuntu에서 `/dev/ttyUSB*`, `/dev/ttyACM*` 접근 권한 때문에 `Permission denied`가 날 수 있습니다.

처음 한 번만 현재 사용자를 `dialout` 그룹에 추가합니다.

```bash
sudo usermod -aG dialout $USER
```

그 다음 **로그아웃 후 다시 로그인**하거나 재부팅합니다.

확인:

```bash
groups
```

출력에 `dialout`이 있으면 됩니다.

### `chmod`를 매번 다시 해야 하는 이유

아래 명령은 임시 해결입니다.

```bash
sudo chmod a+rw /dev/ttyUSB0
```

USB를 뽑으면 기존 `/dev/ttyUSB0` device node가 삭제되고, 다시 꽂을 때 새 device node가 생성됩니다.  
따라서 이전 `chmod` 설정도 사라집니다.

정상적인 영구 해결 방법은 `dialout` 그룹입니다.

급하게 한 번만 테스트할 때:

```bash
sudo chmod a+rw /dev/ttyACM0
sudo chmod a+rw /dev/ttyUSB0
sudo chmod a+rw /dev/ttyUSB1
```

---

## 연결된 센서 포트 찾기

한 번에 확인:

```bash
bash scripts/check_devices.sh
```

직접 확인:

```bash
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
ls -l /dev/serial/by-id/ 2>/dev/null
```

보통 다음과 같이 잡힙니다.

```text
AnySkin                     -> /dev/ttyACM0
CoinFT 하나 + FT232R 하나   -> /dev/ttyUSB0
CoinFT 두 개 + FT232R 두 개 -> /dev/ttyUSB0, /dev/ttyUSB1
```

CoinFT 두 개를 동시에 사용할 때는 `/dev/ttyUSB0`, `/dev/ttyUSB1`보다 다음 경로를 권장합니다.

```text
/dev/serial/by-id/...
```

`ttyUSB0`, `ttyUSB1` 번호는 재연결이나 재부팅 후 바뀔 수 있습니다.

---

# AnySkin

## AnySkin 연결 확인

연결 구조:

```text
AnySkin magnetometer board
    -> QWIIC
    -> Adafruit QT Py
    -> USB
    -> PC
```

USB 연결 후:

```bash
ls -l /dev/ttyACM* 2>/dev/null
```

정상이면 보통:

```text
/dev/ttyACM0
```

가 보입니다.

> 전원만 공급되는 charge-only USB 케이블은 사용할 수 없습니다. 데이터 통신이 가능한 USB 케이블이 필요합니다.

---

## AnySkin 시각화

가장 간단한 확인 방법입니다.

```bash
anyskin_viz /dev/ttyACM0
```

화면에서 5개 magnetometer의 반응을 실시간으로 확인할 수 있습니다.

baseline이 밀렸으면 `B` 키를 눌러 baseline을 다시 잡습니다.

---

## AnySkin raw 15D 읽기

터미널에서 raw 값을 확인:

```bash
python anyskin/read_anyskin.py \
  --port /dev/ttyACM0
```

100개 sample만 확인:

```bash
python anyskin/read_anyskin.py \
  --port /dev/ttyACM0 \
  --count 100
```

10 sample마다 한 번 출력:

```bash
python anyskin/read_anyskin.py \
  --port /dev/ttyACM0 \
  --print-every 10
```

---

## AnySkin CSV 저장

`Ctrl+C`를 누를 때까지 저장:

```bash
python anyskin/record_anyskin_csv.py \
  --port /dev/ttyACM0
```

30초 저장:

```bash
python anyskin/record_anyskin_csv.py \
  --port /dev/ttyACM0 \
  --duration 30
```

저장 위치 지정:

```bash
python anyskin/record_anyskin_csv.py \
  --port /dev/ttyACM0 \
  --duration 30 \
  --output recordings/anyskin_test.csv
```

---

## AnySkin 데이터 형식

AnySkin은 5개의 3축 magnetometer를 사용합니다.

```text
5 magnetometers × 3 axes = 15 values
```

CSV 형식:

```text
host_time
sensor_time
mag0_x mag0_y mag0_z
mag1_x mag1_y mag1_z
...
mag4_x mag4_y mag4_z
```

이 값은 **자기장 기반 tactile raw signal**입니다.

```text
AnySkin raw != Force [N]
```

15개 값을 힘 값으로 해석하면 안 됩니다.

---

## AnySkin 문제 해결

### `/dev/ttyACM0`이 안 보임

먼저 USB 케이블을 확인합니다.

```bash
dmesg | tail -50
```

체크 순서:

```text
1. 데이터 통신 가능한 USB 케이블인가?
2. 다른 USB 포트에서도 동일한가?
3. 연결 직후 dmesg에 장치가 잡히는가?
```

### Permission denied

```bash
groups
```

`dialout`이 있는지 확인합니다.

없다면:

```bash
sudo usermod -aG dialout $USER
```

후 로그아웃/로그인합니다.

### 값의 zero가 밀림

공식 visualizer에서 `B`를 눌러 baseline을 다시 잡습니다.

---

# CoinFT

## 꼭 알아야 할 연결 구조

CoinFT 하나:

```text
CoinFT -> FT232R -> USB -> PC
```

CoinFT 두 개:

```text
Left CoinFT  -> FT232R #1 -> USB -> PC
Right CoinFT -> FT232R #2 -> USB -> PC
```

> **CoinFT 두 개를 FT232R 하나의 UART RX에 합치면 안 됩니다.**

CoinFT native UART packet에는 sensor ID가 없습니다.  
두 센서의 송신선을 하나로 합치면 packet collision이 발생할 수 있으며, 실제로 일정 간격의 spike가 발생했습니다.

각 CoinFT는 반드시 독립적인 UART/FT232R 경로를 사용합니다.

---

## CoinFT 하나 연결 확인

FT232R 하나만 연결한 상태:

```bash
ls -l /dev/ttyUSB*
```

보통:

```text
/dev/ttyUSB0
```

입니다.

Left를 꽂아도 `/dev/ttyUSB0`, Right만 꽂아도 `/dev/ttyUSB0`일 수 있습니다.  
장치가 하나뿐이면 첫 번째 USB serial 장치가 `ttyUSB0`으로 잡히는 것이 정상입니다.

---

## CoinFT raw 12채널 읽기

센서가 직접 보내는 12개 raw channel을 확인합니다.

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode raw
```

모든 packet 출력:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode raw \
  --print-every 1
```

센서/UART 자체가 정상인지 확인할 때 가장 먼저 보는 값입니다.

---

## CoinFT tare-zeroed raw 읽기

초기 baseline을 뺀 12채널 raw 값입니다.

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode zeroed
```

기본 tare:

```text
500 samples
```

tare 중에는 센서를 누르거나 하중을 주지 않습니다.

tare sample 수 변경:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode zeroed \
  --tare-samples 1000
```

---

## CoinFT 6축 F/T 읽기

6축 force/torque 값을 확인합니다.

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode wrench
```

출력:

```text
Fx, Fy, Fz  [N]
Mx, My, Mz  [Nm]
```

raw, zeroed raw, wrench를 한 번에 확인:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode all
```

---

## CoinFT 하나 시각화

### X/Y/Z를 한 그래프에서 보기

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left
```

### Z scale이 커서 X/Y가 잘 안 보일 때

권장 방식:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --split-z
```

Right 센서를 하나만 연결한 경우:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Right \
  --split-z
```

키:

```text
r       Y축 범위 초기화
Ctrl+C  종료
```

---

## CoinFT 두 개 동시 시각화

두 FT232R을 모두 연결합니다.

먼저 고유 ID 확인:

```bash
ls -l /dev/serial/by-id/
```

어느 FT232R이 Left인지, Right인지 한 번 확인한 뒤 사용합니다.

권장:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port /dev/serial/by-id/<LEFT_FTDI_ID> \
  --right-port /dev/serial/by-id/<RIGHT_FTDI_ID> \
  --split-z
```

빠른 테스트:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port /dev/ttyUSB0 \
  --right-port /dev/ttyUSB1 \
  --split-z
```

확인할 것:

```text
Left를 누름  -> Left plot 반응
Right를 누름 -> Right plot 반응
아무것도 안 누름 -> 주기적인 spike 없음
```

---

## CoinFT 하나 CSV 저장

30초 저장:

```bash
python coinft/record_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --duration 30
```

파일명 지정:

```bash
python coinft/record_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --duration 30 \
  --output recordings/coinft_left_test.csv
```

CSV에는 다음이 같이 저장됩니다.

```text
raw 12채널
tare-zeroed raw 12채널
Fx Fy Fz Mx My Mz
```

---

## CoinFT 두 개 CSV 저장

```bash
python coinft/record_coinft_dual.py \
  --left-port /dev/serial/by-id/<LEFT_FTDI_ID> \
  --right-port /dev/serial/by-id/<RIGHT_FTDI_ID> \
  --duration 30
```

두 CoinFT는 서로 독립된 FT232R/UART clock을 사용합니다.

dual recorder는 두 센서를 억지로 같은 row에 맞추지 않고 각 sample의 timestamp를 개별적으로 저장합니다.

---

## CoinFT 데이터 형식

Direct UART 설정:

```text
baud rate : 1,000,000
frame     : 0x02 + 12 × uint16 little-endian + 0x03
payload   : 24 bytes
total     : 26 bytes
```

데이터 처리 순서:

```text
12-channel raw
    ↓
tare subtraction
    ↓
input normalization
    ↓
CFT24_MLP.onnx
    ↓
output denormalization
    ↓
Fx Fy Fz Mx My Mz
```

정리하면:

```text
raw        = CoinFT가 직접 보내는 12채널 값
zeroed raw = tare baseline을 뺀 12채널 값
wrench     = calibration model을 거친 6축 F/T 값
```

single CSV:

```text
host_time
label
raw0 ... raw11
raw_zeroed0 ... raw_zeroed11
Fx_N Fy_N Fz_N
Mx_Nm My_Nm Mz_Nm
```

시각화에는 화면 가독성을 위해 moving average가 적용됩니다.

CSV와 raw reader는 시각화된 smoothing 값이 아니라 원본 sample을 저장/출력합니다.

---

## CoinFT calibration 주의사항

기본 calibration 파일:

```text
coinft/hardware_configs/CFT24_MLP.onnx
coinft/hardware_configs/CFT24_norm.json
```

센서 동작과 상대적인 F/T 반응을 확인하는 데 사용할 수 있습니다.

하지만 포함된 calibration 파일이 **모든 물리 CoinFT unit에서 정확한 절대 N/Nm 값을 보장하는 것은 아닙니다.**

정량적인 force/torque 실험 전에 실제 센서와 calibration 파일의 대응 관계를 확인합니다.

---

## CoinFT 문제 해결

### Permission denied

```bash
groups
```

`dialout` 확인.

없다면:

```bash
sudo usermod -aG dialout $USER
```

후 로그아웃/로그인합니다.

`chmod`를 USB 재연결 때마다 반복하는 방식은 영구 해결이 아닙니다.

### 아무것도 안 건드렸는데 일정 간격으로 spike가 생김

가장 먼저 배선을 확인합니다.

정상:

```text
Left  CoinFT -> FT232R #1
Right CoinFT -> FT232R #2
```

잘못된 구성:

```text
Left  CoinFT --\
                -> FT232R 하나
Right CoinFT --/
```

두 CoinFT의 UART TX를 하나의 FT232R RX로 합치면 안 됩니다.

### 재연결 후 Left/Right가 바뀜

`/dev/ttyUSB0`, `/dev/ttyUSB1`은 센서 ID가 아닙니다.

```bash
ls -l /dev/serial/by-id/
```

dual 사용 시에는 다음 형식을 권장합니다.

```text
/dev/serial/by-id/<FTDI_ID>
```

### 시작하자마자 offset이 큼

tare 중:

```text
센서를 누르지 않기
외력을 주지 않기
```

잘못 tare했다면 프로그램을 다시 실행합니다.

### raw 값은 정상인데 Fx/Fy/Fz/Mx/My/Mz가 이상함

먼저 raw부터 확인:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode raw
```

raw가 안정적이면 다음을 확인합니다.

```text
CFT24_MLP.onnx
CFT24_norm.json
센서별 calibration 대응 여부
```

---

# 권장 검증 순서

새 PC, 새 FT232R, 재배선 후에는 아래 순서로 확인합니다.

## 1. 환경 확인

```bash
conda activate umi-sensor
python scripts/smoke_test.py
```

## 2. 장치 확인

```bash
bash scripts/check_devices.sh
```

## 3. AnySkin 확인

```bash
anyskin_viz /dev/ttyACM0
```

```bash
python anyskin/read_anyskin.py \
  --port /dev/ttyACM0 \
  --count 20
```

확인:

```text
화면 반응 정상
raw 15D 값 변화 정상
```

## 4. CoinFT를 하나씩 확인

한 FT232R만 연결:

```bash
python coinft/read_coinft.py \
  --port /dev/ttyUSB0 \
  --mode raw \
  --count 20 \
  --print-every 1
```

Left:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Left \
  --split-z
```

Left를 빼고 Right만 연결:

```bash
python coinft/visualize_coinft_single.py \
  --port /dev/ttyUSB0 \
  --label Right \
  --split-z
```

확인:

```text
각 센서 단독 동작 정상
주기적 spike 없음
```

## 5. CoinFT 두 개 확인

```bash
ls -l /dev/serial/by-id/
```

Left/Right FT232R ID 확인 후:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port <LEFT_PORT> \
  --right-port <RIGHT_PORT> \
  --split-z
```

확인:

```text
Left/Right 독립적으로 반응
아무것도 안 건드릴 때 periodic spike 없음
```

## 6. 짧게 저장 테스트

AnySkin:

```bash
python anyskin/record_anyskin_csv.py \
  --duration 10
```

CoinFT:

```bash
python coinft/record_coinft_dual.py \
  --left-port <LEFT_PORT> \
  --right-port <RIGHT_PORT> \
  --duration 10
```

`recordings/`에 생성된 CSV를 확인한 뒤 실제 데이터 수집을 시작합니다.

---

# Repository 구조

```text
UMI_sensor_release/
├── README.md
├── README_KR.md
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
└── licenses/
```

추가 protocol 및 troubleshooting 정보는 [`docs/`](docs/)를 참고합니다.

---

# Upstream / License

- AnySkin: https://github.com/raunaqbhirangi/anyskin
- CoinFT: https://github.com/coin-ft/coin-ft

재배포 또는 연구 외 사용 전 [`LICENSE`](LICENSE)와 [`licenses/`](licenses/)를 확인합니다.
