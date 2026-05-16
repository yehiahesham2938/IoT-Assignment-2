
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

# Correct IDs from your dashboard
APPLICATION_ID = "958773be-569a-447d-bd73-1f6b63682bc7"
DEVICE_PROFILE_ID = "f7910ac9-80ee-4026-8b6d-1ed6146d3429"

class ChirpStackDeviceSetup:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        if CHIRPSTACK_API_TOKEN:
            self.session.headers.update({'Authorization': f'Bearer {CHIRPSTACK_API_TOKEN}'})

    def delete_device(self, dev_eui):
        """Delete device if it exists."""
        try:
            url = f"{CHIRPSTACK_API_URL}/devices/{dev_eui}"
            resp = self.session.delete(url, timeout=5)
            if resp.status_code == 200:
                logger.info(f"Deleted existing device {dev_eui}")
            elif resp.status_code != 404:
                logger.warning(f"Delete {dev_eui} returned {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Error deleting {dev_eui}: {e}")

    def create_and_activate_device(self, node_id, zone):
        """Create and activate a device with ABP."""
        device_name = f"SensorNode_{node_id:02d}"
        dev_eui = f"70b3d501{node_id:08x}"
        
        # Consistent credentials
        dev_addr = f"2601{zone:02d}{node_id:02x}"
        nwk_skey = f"000102030405060708090a0b0c0d0e{node_id:02x}"
        app_skey = f"101112131415161718191a1b1c1d1e{node_id:02x}"
        
        # Ensure we have clean slate
        self.delete_device(dev_eui)
        
        device_payload = {
            "device": {
                "applicationId": APPLICATION_ID,
                "description": f"Crop sensor node {node_id} (Zone {zone})",
                "deviceName": device_name,
                "devEUI": dev_eui,
                "deviceProfileId": DEVICE_PROFILE_ID,
                "skipFCntCheck": True, # Crucial for simulation restarts
            }
        }
        
        activation_payload = {
            "deviceActivation": {
                "devAddr": dev_addr,
                "appSKey": app_skey,
                "nwkSKey": nwk_skey,
                "fCntUp": 0,
                "nFCntDown": 0,
                "aFCntDown": 0
            }
        }
        
        try:
            # 1. Create device
            logger.info(f"Creating device {device_name} ({dev_eui})...")
            resp = self.session.post(f"{CHIRPSTACK_API_URL}/devices", json=device_payload)
            if resp.status_code not in [200, 201]:
                logger.error(f"Failed to create: {resp.text}")
                return False
                
            # 2. Activate with ABP
            logger.info(f"Activating device {device_name} with ABP...")
            resp = self.session.post(f"{CHIRPSTACK_API_URL}/devices/{dev_eui}/activate", json=activation_payload)
            if resp.status_code not in [200, 201]:
                logger.error(f"Failed to activate: {resp.text}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    def setup_all(self):
        success = 0
        for zone in range(1, 3):
            for i in range(1, 6):
                node_id = (zone - 1) * 5 + i
                if self.create_and_activate_device(node_id, zone):
                    success += 1
        logger.info(f"Setup complete: {success}/10 devices created and activated.")

if __name__ == '__main__':
    setup = ChirpStackDeviceSetup()
    setup.setup_all()
