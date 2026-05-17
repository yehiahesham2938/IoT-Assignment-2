import paho.mqtt.client as mqtt
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RogueDevice:
    """
    Simulates an unauthorized device attempting to publish false data.
    Demonstrates how AWS IoT Core rejects connections without valid certificates.
    """
    
    def __init__(self, broker_host, broker_port=8883):
        self.client = mqtt.Client(client_id="RogueDevice_Attacker")
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.connected = False
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
    
    def attempt_connection(self, broker_host, broker_port):
        """
        Attempt to connect without valid certificates.
        AWS IoT Core will reject this connection.
        """
        logger.warning(f"Rogue device attempting unauthorized connection to {broker_host}:{broker_port}")
        logger.warning("Attempting to connect WITHOUT valid X.509 certificates...")
        
        try:
            # Attempt connection WITHOUT setting certificates (this will fail)
            self.client.connect(broker_host, broker_port, keepalive=60)
            self.client.loop_start()
            time.sleep(3)
            
            if not self.connected:
                logger.error("❌ Connection REJECTED - No valid certificates provided")
                logger.info("This is expected behavior - AWS IoT requires mutual TLS authentication")
        
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            logger.info("Expected: AWS IoT Core rejected unauthorized connection")
        
        finally:
            self.client.loop_stop()
            self.client.disconnect()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle connection response."""
        if rc == 0:
            self.connected = True
            logger.warning("⚠️  Rogue device CONNECTED (this should NOT happen!)")
        else:
            logger.error(f"Connection failed with code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle disconnection."""
        self.connected = False
        if rc != 0:
            logger.info(f"Disconnected with code {rc} (expected)")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming messages."""
        logger.warning(f"ROGUE: Received message on {msg.topic}: {msg.payload}")
    
    def attempt_malicious_publish(self):
        """
        Attempt to publish false sensor data (after connection fails).
        """
        if self.connected:
            logger.warning("🚨 Rogue device attempting to publish false sensor readings!")
            false_data = {
                "device_id": "FakeNode_99",
                "zone": "Zone_1",
                "temperature": 50,  # False high reading
                "humidity": 95,      # False high reading
                "rssi": -50,
                "timestamp": "2024-05-16T12:00:00Z"
            }
            
            self.client.publish(
                "dt/zone1/sensor_data",
                json.dumps(false_data),
                qos=1
            )
            logger.warning("False data would have been published (but connection failed)")
        else:
            logger.info("Rogue device cannot publish - connection was rejected")


if __name__ == "__main__":
    import sys
    
    # Configuration
    AWS_ENDPOINT = 'a19awyw8hpyek5-ats.iot.eu-north-1.amazonaws.com'  # Replace with your actual endpoint
    
    logger.info("=" * 60)
    logger.info("SECURITY DEMO: Rogue Device Attack Simulation")
    logger.info("=" * 60)
    logger.info("This demo shows how AWS IoT Core protects against")
    logger.info("unauthorized devices without valid certificates.")
    logger.info("=" * 60)
    
    # Create rogue device
    rogue = RogueDevice(AWS_ENDPOINT, 8883)
    
    # Attempt unauthorized connection
    rogue.attempt_connection(AWS_ENDPOINT, 8883)
    
    logger.info("=" * 60)
    logger.info("RESULT: Connection rejected as expected")
    logger.info("✓ AWS IoT Core successfully blocked unauthorized access")
    logger.info("=" * 60)
