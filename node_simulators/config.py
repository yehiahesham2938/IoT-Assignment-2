
# ChirpStack Configuration
CHIRPSTACK_HOST = 'localhost'
CHIRPSTACK_MQTT_PORT = 1884
CHIRPSTACK_API_URL = "http://localhost:8090/api"

# IDs from ChirpStack Dashboard
TENANT_ID = "30a9ed7c-2f02-4699-9d02-a3fa72f7f56f"
APPLICATION_ID = "958773be-569a-447d-bd73-1f6b63682bc7"

# Device Configuration
def get_device_credentials(node_id, zone):
    """
    Generate credentials matching the dashboard DevEUIs.
    """
    device_name = f"SensorNode_{node_id:02d}"
    # Dashboard uses 70b3d50100000001, 70b3d50100000002, etc.
    dev_eui = f"70b3d501{node_id:08x}"
    
    # We use these for the simulation. 
    # NOTE: These MUST be activated in ChirpStack for decryption to work.
    dev_addr = f"2601{zone:02d}{node_id:02x}"
    nwk_skey = f"000102030405060708090a0b0c0d0e{node_id:02x}"
    app_skey = f"101112131415161718191a1b1c1d1e{node_id:02x}"
    
    return {
        'name': device_name,
        'dev_eui': dev_eui,
        'dev_addr': dev_addr,
        'nwk_skey': nwk_skey,
        'app_skey': app_skey
    }

# Transmission Settings
TRANSMISSION_INTERVAL = 30 
