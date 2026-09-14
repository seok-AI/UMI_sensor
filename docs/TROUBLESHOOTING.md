# Troubleshooting

## `Permission denied: /dev/ttyUSB0` or `/dev/ttyACM0`

Recommended permanent fix on Ubuntu:

```bash
sudo usermod -aG dialout $USER
```

Then log out and log back in. Confirm:

```bash
groups
```

Temporary test-only workaround:

```bash
sudo chmod a+rw /dev/ttyUSB0
sudo chmod a+rw /dev/ttyACM0
```

## AnySkin does not appear

Check:

```bash
ls /dev/ | grep -E 'ACM|USB'
lsusb
```

A charge-only USB cable can power the sensor while providing no data connection. Try a known data-capable USB cable.

## CoinFT direct test fails at packet-size query

Check:

```bash
ls -l /dev/ttyUSB*
ls -l /dev/serial/by-id/
```

Expected setup:

```text
CoinFT Left  -> FT232R #1 -> NUC
CoinFT Right -> FT232R #2 -> NUC
```

Each direct CoinFT connection uses 1,000,000 baud.

## Periodic spikes every few seconds

A periodic multi-axis spike was observed when two CoinFT sensor streams were combined onto one FT232/UART. After separating the two sensors onto independent FT232R adapters, the spike disappeared during single-sensor testing.

Do **not** merge two CoinFT TX streams onto one UART. The native direct packet has no sensor ID and simultaneous transmissions can collide.

## `ttyUSB0` and `ttyUSB1` swap after reconnect/reboot

Use stable FTDI IDs:

```bash
ls -l /dev/serial/by-id/
```

Then run the dual visualizer with those paths instead of `/dev/ttyUSB0` and `/dev/ttyUSB1`.

Example:

```bash
python coinft/visualize_coinft_dual.py \
  --left-port /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_XXXXXXXX-if00-port0 \
  --right-port /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_YYYYYYYY-if00-port0 \
  --split-z
```

## CoinFT values drift at startup

Do not touch/load the sensor during tare. For repeatable measurements, allow the hardware to warm up and then rerun the script so tare is performed again.

## Z makes X/Y hard to see

Use:

```bash
--split-z
```

This plots X/Y together and Z on its own Y scale. Press `r` inside the Matplotlib window to reset display ranges.
