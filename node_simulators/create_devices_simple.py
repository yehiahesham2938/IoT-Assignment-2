"""
ChirpStack Device Creation - Fixed API format
Creates 10 LoRaWAN devices with ABP activation
"""

import requests
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_BASE = "http://localhost:8090/api"
TENANT_ID = "30a9ed7c-2f02-4699-9d02-a3fa72f7f56f"
APPLICATION_ID = "958773be-569a-447d-bd73-1f6b63682bc7"

class DeviceCreator:
    def __init__(self):
        self.session = requests.Session()
    
    def list_device_profiles(self):
        """Get available device profiles."""
        try:
            response = self.session.get(f"{API_BASE}/device-profiles?limit=10", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    return data['result']
                return []
            logger.error(f"Failed to get device profiles: {response.text}")
            return []
        except Exception as e:
            logger.error(f"Error getting device profiles: {e}")
            return []
    
    def create_device_simple(self, node_num, zone):
        """Create a device with minimum required fields."""
        device_name = f"SensorNode_{node_num:02d}"
        dev_eui = f"70b3d5{node_num:08x}"[:16]  # 16 hex characters
        
        # The simplest payload
        payload = {
            "name": device_name,
            "description": f"Crop sensor node {node_num} (Zone {zone})",
            "devEUI": dev_eui,
            "skipFCntCheck": False
        }
        
        try:
            logger.info(f"Creating {device_name}...")
            url = f"{API_BASE}/applications/{APPLICATION_ID}/devices"
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                device_id = result.get('deviceID') or result.get('id')
                logger.info(f"✓ {device_name} created (ID: {device_id})")
                return True
            else:
                logger.error(f"✗ Failed: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return False


def create_all_devices():
    """Create all 10 devices."""
    logger.info("=" * 70)
    logger.info("Creating 10 LoRaWAN Devices for Crop Disease Network")
    logger.info("=" * 70)
    
    creator = DeviceCreator()
    
    # List available device profiles first
    logger.info("\nChecking available device profiles...")
    profiles = creator.list_device_profiles()
    if profiles:
        logger.info(f"Found {len(profiles)} device profiles")
        for p in profiles[:3]:  # Show first 3
            logger.info(f"  - {p.get('name', 'Unknown')}")
    else:
        logger.warning("No device profiles found - create a default one in ChirpStack first")
    
    logger.info("\n" + "=" * 70)
    
    success = 0
    for zone in range(1, 3):
        logger.info(f"\nZone {zone}:")
        for i in range(1, 6):
            node_num = (zone - 1) * 5 + i
            if creator.create_device_simple(node_num, zone):
                success += 1
    
    logger.info("\n" + "=" * 70)
    logger.info(f"Result: {success}/10 devices created")
    logger.info("=" * 70)


if __name__ == "__main__":
    create_all_devices()
