# Smart-Room-EM

This project reads energy meter values over a Modbus RTU serial connection and sends them to a OneM2M endpoint (via `Om2mHandler.create_cin`). It includes a compact script `sr-em.py` which contains the Modbus polling logic and a sample `CONFIG` dictionary for meter/register mapping.

**Note:** This README explains the project from basics through meter configuration and troubleshooting.

**Repository Structure**
- `sr-em.py`: Main script that reads Modbus registers and calls `create_cin` to forward data.
- `Om2mHandler.py`: Handler used to create OneM2M content instances (CIN). The handler implementation is expected to expose a `create_cin` function.
- `requirements.txt`: Python dependencies used by the project.
- `sr-em.config`: Optional external configuration (if you choose to implement / load it). Not required by the provided `sr-em.py` which uses an inline `CONFIG`.

**Quick Goals**
- Poll Modbus RTU meters (energy, power, voltage, current, etc.).
- Format and send measurements to OneM2M using `create_cin`.

**Prerequisites**
- Python 3.8+ installed on your machine.
- A USB-to-RS485 (or USB-to-RS232) adapter compatible with your meters.
- Meters configured for Modbus RTU.

**Installation**
1. Create and activate a virtual environment (macOS / Linux):

```
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```
pip install -r requirements.txt
```


**Configuration (Basic)**

```
    "modbus": {
        "port": "/dev/ttyUSB0",
        "baudrate": 19200,
        "bytesize": 8,
        "parity": "E",
        "stopbits": 1,
        "timeout": 2.0
    },
```

Open `sr-em.py` and inspect the `CONFIG` dictionary near the top. Important keys:

- `modbus`:
  - `port`: Serial device path. On Linux use `/dev/ttyUSBx` (for example `/dev/ttyUSB0`).
  - `baudrate`: e.g. `19200`.
  - `bytesize`, `parity`, `stopbits`, `timeout`: typical Modbus settings — the defaults in `sr-em.py` are common for many meters (8, `E`, 1, 2.0).

- `nodes`: A mapping of Modbus slave IDs to the registers you want to read. Example from `sr-em.py`:

```
    "nodes": {
        1: {"Energy": 3960, "Power": 3902, "Current": 3912},
        2: {"Energy": 158, "Power": 100, "Voltage": 140, "Current": 148, "Frequency": 156, "PowerFactor": 116},
        3: {"Energy": 158, "Power": 100, "Voltage": 140, "Current": 148, "Frequency": 156, "PowerFactor": 116},
    }
```

- `read_interval`: Polling interval in seconds.

How `nodes` is used:
- Keys of the inner dict are the human-friendly measurement names (strings).
- Values are Modbus register addresses (integers) that the meter stores the given measurement in.

**How `sr-em.py` reads values (endianness & format)**

`sr-em.py` uses `pymodbus` to read holding registers and the following packing/unpacking:

```
struct.unpack(">f", struct.pack(">HH", regs[1], regs[0]))[0]
```

This means:
- The code expects 32-bit IEEE float values stored in two consecutive 16-bit Modbus registers.
- It swaps the two 16-bit words before interpreting them as a big-endian float (word order swapped). That is, it reads registers [addr, addr+1] but constructs the float from `regs[1]` then `regs[0]`.

Why this matters:
- Different meters use different word/byte orders. If your floats are wrong (very large/NaN/zero), try either swapping the words (as in the code) or using the natural order depending on your meter documentation.

Reading behaviour summary:
- The `read_register` helper requests `count=2` registers starting at the configured address.
- If read succeeds it converts the returned two 16-bit registers into a 32-bit float using the swapped-word approach.
- On errors it prints a warning and returns `0.0` for that measurement.

**Example `nodes` entry and ordering**
The script, for each node, builds a `send_list` like this:

```
[ timestamp, value_for_first_key_in_regs, value_for_second_key, ... ]
```

Note: the ordering of the measurement values in the sent list matches the iteration order of `regs.keys()` in `CONFIG`. If you rely on a specific order at the receiving side, make sure to keep the dict key order stable (Python 3.7+ preserves insertion order).

**OneM2M integration**
- `sr-em.py` calls `create_cin(meter_id, send_list)` from `Om2mHandler.py`.
- `create_cin` is expected to accept:
  - `meter_id`: numeric identifier of the meter (same as the Modbus slave ID).
  - `send_list`: list where the first element is a timestamp (UNIX epoch int), followed by measurement floats in the same order as `CONFIG['nodes'][meter_id]`.

If you need to adapt payload structure, edit `sr-em.py` to shape `send_list` differently or update `Om2mHandler.create_cin` accordingly.

**Running the script**
From the project folder with the venv activated:

```
python sr-em.py
```

**Finding serial ports**
To find serial devices on Linux/macOS, check `/dev/` entries (for example `/dev/ttyUSB0`, `/dev/ttyS0`, or `/dev/ttyACM0`). On many systems `dmesg` and `ls /dev/tty*` are useful.

```
ls /dev/tty*
dmesg | grep -i tty
```

**Testing without hardware (simulation)**
- You can simulate Modbus responses by mocking `pymodbus` calls or by creating a small script that emulates the slave device. For quick tests, temporarily modify `read_modbus_values` to return fixed values instead of reading the serial port.

Example quick change for testing (not permanent):

```
def read_modbus_values(slave_id, registers):
    return {name: float(idx) * 1.234 for idx, name in enumerate(registers.keys(), start=1)}
```

**Common Troubleshooting**
- Serial connection fails:
  - **Check**: `CONFIG['modbus']['port']` and the adapter LED/connection.
  - **Check**: Ensure no other program (serial terminal) has the serial port open.
  - **Permissions**: On Linux you'll often need `dialout`/tty permissions (use `sudo` or add your user to the `dialout` group).

- Reads give `0.0` or NaNs:
  - **Check**: Correct register addresses and correct number format (32-bit float vs 32-bit signed int / two 16-bit ints).
  - **Try**: Changing word order (swap words or bytes) to match your meter.

- Unexpected values:
  - Cross-check the meter datasheet for register map, scaling factors (some meters use LSB scaling for energy), and data type.

**Extending / Adding new meters**
1. Add a new entry under `CONFIG['nodes']` with the slave ID as the key and a dict of measurement name -> register address as value.
2. Confirm the meter stores values as 32-bit floats (or adjust the code to read integers and apply scaling).
3. If your meter uses holding registers at half-word offsets (e.g., energy split across multiple registers with scaling), implement a custom read and conversion function in `sr-em.py`.

**Logging and Improvements**
- Consider adding structured logging instead of prints (Python `logging` module).
- Add a configuration loader to read `sr-em.config` or a JSON/YAML file so you don't edit `sr-em.py` directly.
- Add command-line flags to choose a single meter to poll for debugging.

**Contributing**
- Make changes in a branch, add tests if you change logic, and open a PR describing the change.

**License**
- Add your preferred license if you intend to share the project publicly.

---

If you'd like, I can:
- add a configuration loader for `sr-em.config` (YAML/JSON),
- add a mock mode for offline testing, or
- update `Om2mHandler.py` to include a stub `create_cin` for local testing.

Tell me which of those you want next and I will implement it.

