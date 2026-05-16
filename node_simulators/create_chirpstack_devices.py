"""
Automatic device creation script for ChirpStack IoT Assignment 2.
Creates 10 LoRaWAN devices with proper activation credentials.
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ChirpStack configuration
API_URL = "http://localhost:8090/api"
TENANT_ID = "30a9ed7c-2f02-4699-9d02-a3fa72f7f56f"
APPLICATION_ID = "958773be-569a-447d-bd73-1f6b63682bc7"

# You can get an API token from ChirpStack UI if needed
# Format: Authorization: Bearer <token>
API_TOKEN = ""  # Leave empty if ChirpStack doesn't require auth

class ChirpStackAPIClient:
    def __init__(self, api_url, api_token=""):
        self.api_url = api_url
        self.session = requests.Session()
        if api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            })
        else:
            self.session.headers.update({
                'Content-Type': 'application/json'
            })
    
    def create_device(self, app_id, device_name, dev_eui, dev_addr, app_skey, nwk_skey, description=""):
        """Create a device in ChirpStack with ABP activation."""
        payload = {
            "device": {
                "applicationId": app_id,
                "deviceName": device_name,
                "description": description,
                "devEUI": dev_eui,
                "deviceProfileId": "1",  # Default profile
                "skipFCntCheck": False,
                "referenceAltitude": 0,
                "variables": {},
                "tags": {
                    "zone": description.split("Zone")[-1].strip() if "Zone" in description else "",
                    "type": "crop_sensor"
                }
            },
            "deviceStatus": {
                "externalAltitude": 0,
                "externalBattery": 100,
                "externalMargin": 10,
                "latitude": 0,
                "longitude": 0
            }
        }
        
        try:
            endpoint = f'{self.api_url}/devices'
            logger.info(f"Creating device: {device_name}...")
            response = self.session.post(endpoint, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                device_id = response.json().get("id")
                logger.info(f"✓ Device '{device_name}' created (ID: {device_id})")
                
                # Now activate the device with ABP credentials
                self.activate_device_abp(app_id, device_id, dev_addr, nwk_skey, app_skey)
                return True
            else:
                logger.error(f"✗ Failed to create device '{device_name}'")
                logger.error(f"  Status: {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"✗ Error creating device: {e}")
            return False
    
    def activate_device_abp(self, app_id, device_id, dev_addr, nwk_skey, app_skey):
        """Activate device with ABP (Activation by Personalization) credentials."""
        payload = {
            "deviceActivation": {
                "deviceAddr": dev_addr,
                "appSKey": app_skey,
                "nwkSKey": nwk_skey,
                "fCntUp": 0,
                "nFCntDown": 0,
                "aFCntDown": 0
            }
        }
        
        try:
            endpoint = f'{self.api_url}/devices/{device_id}/activation'
            response = self.session.post(endpoint, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info(f"✓ Device activated with ABP credentials")
                logger.info(f"  - Dev Addr: {dev_addr}")
                logger.info(f"  - NwkSKey: {nwk_skey}")
                logger.info(f"  - AppSKey: {app_skey}")
                return True
            else:
                logger.error(f"✗ Failed to activate device")
                logger.error(f"  Response: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"✗ Error activating device: {e}")
            return False


def setup_devices():
    """Create all 10 devices for the project."""
    logger.info("=" * 70)
    logger.info("ChirpStack Device Setup - Crop Disease Early Warning Network")
    logger.info("=" * 70)
    logger.info(f"API URL: {API_URL}")
    logger.info(f"Application ID: {APPLICATION_ID}")
    logger.info("")
    
    client = ChirpStackAPIClient(API_URL, API_TOKEN)
    
    success_count = 0
    nodes_per_zone = 5
    
    for zone in range(1, 3):
        logger.info(f"\n{'='*70}")
        logger.info(f"Zone {zone} - Creating {nodes_per_zone} devices")
        logger.info(f"{'='*70}")
        
        for i in range(1, nodes_per_zone + 1):
            node_id = (zone - 1) * nodes_per_zone + i
            
            # Generate unique but deterministic credentials
            device_name = f"SensorNode_{node_id:02d}"
            dev_eui = f"70b3d5{node_id:02x}{'0' * 8}".lower()[:16]  # 16 hex chars
            dev_addr = f"2601{zone:02d}{node_id:02x}{'0' * 2}".lower()  # 8 hex chars
            nwk_skey = f"000102030405060708090a0b0c0d0e{node_id:02x}".lower()  # 32 hex chars
            app_skey = f"101112131415161718191a1b1c1d1e{node_id:02x}".lower()  # 32 hex chars
            
            description = f"Crop sensor node {node_id} (Zone {zone})"
            
            if client.create_device(
                APPLICATION_ID,
                device_name,
                dev_eui,
                dev_addr,
                app_skey,
                nwk_skey,
                description
            ):
                success_count += 1
            
            logger.info("")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"Setup Complete: {success_count}/10 devices created")
    logger.info("=" * 70)
    logger.info("\nNow you can run the simulator:")
    logger.info("  python run_simulator.py")
    logger.info("=" * 70)
    
    return success_count == 10


if __name__ == '__main__':
    setup_devices()
