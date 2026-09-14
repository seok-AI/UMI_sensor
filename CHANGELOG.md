# Changelog

## 2026-09-14

- Created clean GitHub-ready AnySkin + CoinFT runtime bundle.
- Removed local `.venv`, nested upstream `.git`, and CoinFT calibration training datasets.
- Added one-environment setup for AnySkin and CoinFT runtime.
- Added AnySkin raw read and CSV recording examples.
- Added CoinFT direct FT232R protocol wrapper with packet-size query.
- Added CoinFT raw / tare-zeroed / calibrated wrench reader.
- Added single and dual CoinFT visualizers with optional Z-axis separation.
- Added single and dual CSV recording.
- Documented independent-FT232 requirement and periodic-spike failure mode observed with a shared UART.
- Added serial permission and stable `/dev/serial/by-id` guidance.
