# om2m.py
import requests
import json
from dotenv import load_dotenv
import os
# from blink import blink   # Optional hardware LED indicator

# ✅ Load credentials from .env file
load_dotenv()

DEV_CREDENTIALS = {
    "username": os.getenv("ONEM2M_USERNAME", "default_user"),
    "password": os.getenv("ONEM2M_PASSWORD", "default_pass")
}
# ✅ Each meter has its own endpoint and labels
METER_CONFIG = {
    1: {
        "url": "http://onem2m.iiit.ac.in:443/~/in-cse/in-name/AE-SR/SR-EM/SR-EM-KH04-00/Data",
        "labels": ["AE-SR-EM", "SR-EM-KH04-00", "V1.0.0", "SR-EM-V1.0.0"]
    },
    2: {
        "url": "http://onem2m.iiit.ac.in:443/~/in-cse/in-name/AE-SR/SR-EM/SR-EM-KH04-01/Data",
        "labels": ["AE-SR-EM", "SR-EM-KH04-01", "V2.0.0", "SR-EM-V2.0.0"]
    },
    3: {
        "url": "http://onem2m.iiit.ac.in:443/~/in-cse/in-name/AE-SR/SR-EM/SR-EM-KH04-02/Data",
        "labels": ["AE-SR-EM", "SR-EM-KH04-02", "V2.0.0", "SR-EM-V2.0.0"]
    }
}


def create_cin(meter_id, value, data_format="json", credentials=DEV_CREDENTIALS):
    """
    Sends one data instance (CIN) to the OneM2M container of the given meter_id.
    """
    if meter_id not in METER_CONFIG:
        print(f"❌ Invalid meter ID: {meter_id}")
        return

    uri_cnt = METER_CONFIG[meter_id]["url"]
    cin_labels = METER_CONFIG[meter_id]["labels"]

    headers = {
        "X-M2M-Origin": f"{credentials['username']}:{credentials['password']}",
        "Content-type": f"application/{data_format};ty=4"
    }

    body = {
        "m2m:cin": {
            "con": f"{value}",
            "lbl": cin_labels,
            "cnf": "text"
        }
    }

    try:
        response = requests.post(uri_cnt, json=body, headers=headers)
        if response.status_code == 201:
            print(f"✅ Data sent successfully → {cin_labels[1]}")
            print('Return code : {}'.format(response.status_code))
            print('Return Content : {}'.format(response.text))
          
        else:
            print(f"⚠️ Failed ({response.status_code}) for {cin_labels[1]}: {response.text}")
    except Exception as e:
        print(f"❌ Error sending to {cin_labels[1]}: {e}")


if __name__ == "__main__":
    # 🧪 Test sending sample data for all 3 meters
    test_data = [1759719120, 577060928.00, 9508.23, 17.87]
    for mid in METER_CONFIG:
        create_cin(mid, test_data)
