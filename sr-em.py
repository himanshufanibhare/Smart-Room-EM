# sr-em.py
import struct
import time
from pymodbus.client import ModbusSerialClient
from Om2mHandler import create_cin

CONFIG = {
    "modbus": {
        "port": "/dev/ttyUSB0",
        "baudrate": 19200,
        "bytesize": 8,
        "parity": "E",
        "stopbits": 1,
        "timeout": 2.0
    },

    "nodes": {
        1: {"Energy": 3960, "Power": 3902, "Current": 3912},
        2: {"Energy": 158, "Power": 100, "Voltage": 140, "Current": 148, "Frequency": 156, "PowerFactor": 116},
        3: {"Energy": 158, "Power": 100, "Voltage": 140, "Current": 148, "Frequency": 156, "PowerFactor": 116},
    },

    "read_interval": 60
}


def read_modbus_values(slave_id, registers):
    """Reads configured Modbus registers from a given slave ID."""
    client = ModbusSerialClient(
        port=CONFIG["modbus"]["port"],
        baudrate=CONFIG["modbus"]["baudrate"],
        parity=CONFIG["modbus"]["parity"],
        stopbits=CONFIG["modbus"]["stopbits"],
        bytesize=CONFIG["modbus"]["bytesize"],
        timeout=CONFIG["modbus"]["timeout"]
    )

    if not client.connect():
        print(f"❌ Failed to connect to {CONFIG['modbus']['port']}")
        return {}

    def read_register(address, count=2):
        try:
            result = client.read_holding_registers(address, count, slave_id)
            if result and not result.isError():
                regs = result.registers
                return struct.unpack(">f", struct.pack(">HH", regs[1], regs[0]))[0]
        except Exception as e:
            print(f"⚠️ Error reading addr {address} from unit {slave_id}: {e}")
        return 0.0

    data = {}
    for name, addr in registers.items():
        data[name] = round(read_register(addr), 3)

    client.close()
    return data


if __name__ == "__main__":
    while True:
        timestamp = int(time.time())

        for meter_id, regs in CONFIG["nodes"].items():
            print(f"\n🔹 Reading data from Meter ID: {meter_id}")
            data = read_modbus_values(meter_id, regs)
            print(f"Meter {meter_id} Data: {data}")

            # Create list to send
            send_list = [timestamp]
            for key in regs.keys():
                send_list.append(data.get(key, 0.0))

            print(f"📤 Sending to OneM2M: {send_list}")
            create_cin(meter_id, send_list)

        print(f"\n⏳ Waiting {CONFIG['read_interval']} seconds before next read...\n")
        time.sleep(CONFIG["read_interval"])
