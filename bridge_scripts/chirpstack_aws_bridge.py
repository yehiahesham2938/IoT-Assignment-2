import paho.mqtt.client as mqtt
import json
import logging
import time
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChirpStackAWSBridge:
    """
    Bridge connecting ChirpStack MQTT to AWS IoT Core.
    """
    
    def __init__(self, chirpstack_host, aws_endpoint, cert_path, key_path, ca_path):
        """
        Initialize the bridge.
        
        Args:
            chirpstack_host: ChirpStack MQTT broker host (localhost)
            aws_endpoint: AWS IoT endpoint (xxxxx-ats.iot.REGION.amazonaws.com)
            cert_path: Path to device certificate
            key_path: Path to private key
            ca_path: Path to CA certificate
        """
        self.chirpstack_host = chirpstack_host
        self.aws_endpoint = aws_endpoint
        
        # ChirpStack MQTT client
        self.cs_client = mqtt.Client(client_id="cs_aws_bridge")
        self.cs_client.on_connect = self._cs_on_connect
        self.cs_client.on_message = self._cs_on_message
        self.cs_client.on_disconnect = self._cs_on_disconnect
        
        # AWS IoT MQTT client
        self.aws_client = AWSIoTMQTTClient("CropBridge")
        self.aws_client.configureEndpoint(aws_endpoint, 8883)
        self.aws_client.configureCredentials(ca_path, key_path, cert_path)
        self.aws_client.configureOfflinePublishQueueing(-1)
        self.aws_client.configureDrainingFrequency(2)
        self.aws_client.configureConnectDisconnectTimeout(10)
        self.aws_client.configureMQTTOperationTimeout(5)
        
        self.connected_cs = False
        self.connected_aws = False
    
    def start(self):
        """Start the bridge."""
        logger.info("Starting ChirpStack-AWS Bridge...")
        
        # Connect to AWS first
        try:
            self.aws_client.connect()
            self.connected_aws = True
            logger.info("Connected to AWS IoT Core")
        except Exception as e:
            logger.error(f"AWS connection failed: {e}")
            return False
        
        # Connect to ChirpStack
        try:
            self.cs_client.connect(self.chirpstack_host, 1883, keepalive=60)
            self.cs_client.loop_start()
        except Exception as e:
            logger.error(f"ChirpStack connection failed: {e}")
            return False
        
        # Wait for ChirpStack connection
        timeout = 10
        start = time.time()
        while not self.connected_cs and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        if self.connected_cs:
            logger.info("Bridge started successfully")
            return True
        else:
            logger.error("Failed to connect to ChirpStack")
            return False
    
    def stop(self):
        """Stop the bridge."""
        logger.info("Stopping bridge...")
        self.cs_client.loop_stop()
        self.cs_client.disconnect()
        self.aws_client.disconnect()
        logger.info("Bridge stopped")
    
    def _cs_on_connect(self, client, userdata, flags, rc):
        """ChirpStack connection callback."""
        if rc == 0:
            self.connected_cs = True
            logger.info("Connected to ChirpStack MQTT broker")
            # Subscribe to all device uplink messages
            client.subscribe("application/+/device/+/event/up")
        else:
            logger.error(f"ChirpStack connection failed: {rc}")
    
    def _cs_on_disconnect(self, client, userdata, rc):
        """ChirpStack disconnection callback."""
        self.connected_cs = False
        if rc != 0:
            logger.warning(f"Unexpected ChirpStack disconnection: {rc}")
    
    def _cs_on_message(self, client, userdata, msg):
        """Handle incoming ChirpStack message."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"ChirpStack message: {msg.topic}")
            
            # Extract device information
            topic_parts = msg.topic.split('/')
            application_id = topic_parts[1]
            device_name = topic_parts[3]
            
            # Extract telemetry from payload
            device_eui = payload.get('deviceInfo', {}).get('devEui')
            dev_addr = payload.get('devAddr', '')
            data = payload.get('data', '')
            
            # Convert device info to zone (assuming naming convention)
            zone = 1 if int(device_name.split('_')[-1]) <= 5 else 2
            
            # Create AWS IoT message
            aws_payload = {
                'device_id': device_name,
                'device_eui': device_eui,
                'zone': zone,
                'dev_addr': dev_addr,
                'data': data,
                'rssi': payload.get('txInfo', {}).get('rssi', 0),
                'snr': payload.get('txInfo', {}).get('snr', 0),
                'timestamp': payload.get('time', '')
            }
            
            # Publish to AWS IoT Core
            aws_topic = f"dt/zone{zone}/telemetry"
            self.aws_client.publish(aws_topic, json.dumps(aws_payload), 1)
            logger.info(f"Forwarded: {device_name} -> AWS ({aws_topic})")
        
        except Exception as e:
            logger.error(f"Message processing error: {e}", exc_info=True)


if __name__ == "__main__":
    import sys
    
    # Configuration
    CHIRPSTACK_HOST = 'localhost'
    AWS_ENDPOINT = 'YOUR_AWS_ENDPOINT.iot.REGION.amazonaws.com'
    CERT_PATH = 'path/to/cert.pem'
    KEY_PATH = 'path/to/key.pem'
    CA_PATH = 'path/to/ca.pem'
    
    # Create and start bridge
    bridge = ChirpStackAWSBridge(
        CHIRPSTACK_HOST,
        AWS_ENDPOINT,
        CERT_PATH,
        KEY_PATH,
        CA_PATH
    )
    
    if bridge.start():
        logger.info("Bridge is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            bridge.stop()
    else:
        logger.error("Failed to start bridge")
        sys.exit(1)
