
import paho.mqtt.client as mqtt
import json
import logging
import time
from datetime import datetime
import lorawan_utils
from lora_frame_encoder import LoRaFrameEncoder

logger = logging.getLogger(__name__)

class ChirpStackMQTTClient:
    """
    MQTT client that simulates a LoRaWAN Gateway to inject data into ChirpStack.
    """
    
    def __init__(self, broker_host='localhost', broker_port=1883, 
                 application_id='', device_id='', gateway_id='0000000000000001'):
        """
        Initialize MQTT client connection.
        
        Args:
            broker_host: ChirpStack MQTT broker address
            broker_port: MQTT broker port (1883 for non-encrypted)
            application_id: ChirpStack application ID
            device_id: Device EUI (hex string)
            gateway_id: Gateway ID (hex string)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.application_id = application_id
        self.dev_eui = device_id
        self.gateway_id = gateway_id
        
        # ChirpStack v4 Gateway Bridge topic (MQTT backend)
        # Structure: [topic_prefix]/gateway/[gateway_id]/event/[event_type]
        self.topic = f"eu868/gateway/{self.gateway_id}/event/up"
        
        # Initialize MQTT client
        self.client = mqtt.Client(client_id=f"gw_sim_{self.dev_eui}_{int(time.time())}")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.connected = False
        
        # Tracking frame counter for LoRaWAN
        self.f_cnt = 0
    
    def connect(self):
        """Connect to ChirpStack MQTT broker."""
        try:
            logger.info(f"Connecting to MQTT Broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.1)
            
            return self.connected
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def publish_telemetry(self, telemetry_payload):
        """
        Publish telemetry as a LoRaWAN Uplink Frame.
        """
        from config import get_device_credentials
        
        # 1. Get credentials for this device
        # We need to find the node_id and zone from the payload or EUI
        # For now, let's assume we can get them from the payload
        node_id = telemetry_payload.get('node_id', 1)
        zone = telemetry_payload.get('zone', 1)
        creds = get_device_credentials(node_id, zone)
        
        # 2. Encode application payload (binary)
        app_payload = LoRaFrameEncoder.encode_telemetry(telemetry_payload)
        
        # 3. Build LoRaWAN ABP Packet (Base64 encoded)
        phy_payload = lorawan_utils.build_abp_packet(
            dev_addr=creds['dev_addr'],
            nwk_skey=creds['nwk_skey'],
            app_skey=creds['app_skey'],
            f_cnt=self.f_cnt,
            f_port=10,
            payload_bytes=app_payload
        )
        
        # 4. Construct Gateway Uplink Frame (JSON format for ChirpStack v4)
        gateway_payload = {
            "phyPayload": phy_payload,
            "txInfo": {
                "frequency": 868100000,
                "modulation": {
                    "lora": {
                        "bandwidth": 125000,
                        "spreadingFactor": 7,
                        "codeRate": "CR_4_5"
                    }
                }
            },
            "rxInfo": {
                "gatewayId": self.gateway_id,
                "uplinkId": f"{int(time.time())}",
                "rssi": -50,
                "snr": 10,
                "location": {
                    "latitude": 0,
                    "longitude": 0
                }
            }
        }
        
        self.f_cnt += 1
        
        # 5. Publish to Gateway Bridge topic
        result = self.client.publish(self.topic, json.dumps(gateway_payload), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published Gateway Uplink for {self.dev_eui}")
            return True
        else:
            logger.error(f"Publish failed: {mqtt.error_string(result.rc)}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("MQTT Broker connected")
        else:
            logger.error(f"MQTT Broker connection failed: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
    
    def _on_publish(self, client, userdata, mid):
        pass