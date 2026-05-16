
import requests
import json
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ChirpStack API configuration
CHIRPSTACK_HOST = 'localhost'
CHIRPSTACK_REST_PORT = 8090
CHIRPSTACK_API_URL = f'http://{CHIRPSTACK_HOST}:{CHIRPSTACK_REST_PORT}/api'

# ChirpStack credentials
CHIRPSTACK_API_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6ImY0MzgyNjc3LWJmODQtNDgxNS1iYzg3LTFlOTRjMThhZDlmYyIsInR5cCI6ImtleSJ9.i9pdRbhaDtycaOHzlwXDtdUfJAyiV50iTseohprhEBM'

class ChirpStackDeviceSetup:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHIRPSTACK_API_TOKEN}'
        })

    def activate_device(self, node_id, zone):
        """Activate an existing device with ABP."""
        dev_eui = f"70b3d501{node_id:08x}"
        dev_addr = f"2601{zone:02d}{node_id:02x}"
        nwk_skey = f"000102030405060708090a0b0c0d0e{node_id:02x}"
        app_skey = f"101112131415161718191a1b1c1d1e{node_id:02x}"
        
        activation_payload = {
            "devAddr": dev_addr,
            "appSKey": app_skey,
            "nwkSKey": nwk_skey,
            "fCntUp": 0,
            "nFCntDown": 0,
            "aFCntDown": 0
        }
        
        try:
            logger.info(f"Activating device {dev_eui}...")
            # Correct endpoint in v4 is /devices/{dev_eui}/activation
            url = f"{CHIRPSTACK_API_URL}/devices/{dev_eui}/activation"
            resp = self.session.post(url, json=activation_payload, timeout=10)
            
            if resp.status_code in [200, 201]:
                logger.info(f"✓ Device {dev_eui} activated")
                return True
            else:
                logger.error(f"✗ Failed to activate {dev_eui}: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    def activate_all(self):
        success = 0
        for zone in range(1, 3):
            for i in range(1, 6):
                node_id = (zone - 1) * 5 + i
                if self.activate_device(node_id, zone):
                    success += 1
        logger.info(f"Activation complete: {success}/10 devices activated.")

if __name__ == '__main__':
    setup = ChirpStackDeviceSetup()
    setup.activate_all()
