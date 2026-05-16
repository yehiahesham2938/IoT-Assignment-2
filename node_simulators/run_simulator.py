import threading
import time
import logging
import signal
import sys
from sensor_node_base import SensorNode
from chirpstack_mqtt_client import ChirpStackMQTTClient
from lora_frame_encoder import LoRaFrameEncoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)-10s] - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import CHIRPSTACK_HOST, CHIRPSTACK_MQTT_PORT, APPLICATION_ID, TRANSMISSION_INTERVAL, get_device_credentials

class NodeSimulator:
    """Manages all 10 sensor nodes and their transmissions."""
    
    def __init__(self, num_nodes=10, zones=2):
        self.num_nodes = num_nodes
        self.zones = zones
        self.nodes = []
        self.threads = []
        self.running = True
        self.mqtt_clients = {}
    
    def initialize_nodes(self):
        """Initialize all sensor nodes and connect to MQTT."""
        nodes_per_zone = self.num_nodes // self.zones
        
        for zone in range(1, self.zones + 1):
            gateway_id = f"000000000000000{zone}"
            
            for i in range(1, nodes_per_zone + 1):
                node_id = (zone - 1) * nodes_per_zone + i
                # Get credentials from shared config
                creds = get_device_credentials(node_id, zone)
                device_eui = creds['dev_eui']
                
                # Create sensor node
                node = SensorNode(
                    node_id=node_id,
                    zone=zone,
                    gateway_id=gateway_id
                )
                node.device_eui = device_eui # Ensure node uses correct EUI
                self.nodes.append(node)
                
                # Create MQTT client for this node
                # Use DevEUI as the device_id in the MQTT client as per ChirpStack standards
                mqtt_client = ChirpStackMQTTClient(
                    broker_host=CHIRPSTACK_HOST,
                    broker_port=CHIRPSTACK_MQTT_PORT,
                    application_id=APPLICATION_ID,
                    device_id=device_eui,
                    gateway_id=gateway_id
                )
                
                if mqtt_client.connect():
                    self.mqtt_clients[node_id] = mqtt_client
                    logger.info(f"Node {node_id} MQTT client connected")
                else:
                    logger.error(f"Node {node_id} MQTT connection failed")
    
    def run_node_transmission(self, node_id):
        """Simulate continuous transmission from a single node."""
        node = next((n for n in self.nodes if n.node_id == node_id), None)
        mqtt_client = self.mqtt_clients.get(node_id)
        
        if not node or not mqtt_client:
            logger.error(f"Node {node_id} not found")
            return
        
        transmission_count = 0
        
        while self.running:
            try:
                # Generate telemetry
                telemetry = node.generate_telemetry()
                
                # Publish via MQTT
                if mqtt_client.publish_telemetry(telemetry):
                    transmission_count += 1
                    logger.info(f"Node {node_id} transmission #{transmission_count}")
                
                # Wait for next transmission
                time.sleep(TRANSMISSION_INTERVAL)
            
            except Exception as e:
                logger.error(f"Node {node_id} transmission error: {e}")
                time.sleep(5)
    
    def start_all_nodes(self):
        """Start transmission threads for all nodes."""
        self.initialize_nodes()
        logger.info(f"Starting {self.num_nodes} sensor nodes...")
        
        for node in self.nodes:
            thread = threading.Thread(
                target=self.run_node_transmission,
                args=(node.node_id,),
                name=f"Node-{node.node_id:02d}",
                daemon=True
            )
            self.threads.append(thread)
            thread.start()
        
        logger.info(f"All {self.num_nodes} nodes started")
    
    def stop_all_nodes(self):
        """Stop all node transmissions."""
        self.running = False
        logger.info("Stopping all nodes...")
        
        # Disconnect MQTT clients
        for mqtt_client in self.mqtt_clients.values():
            mqtt_client.disconnect()
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
        
        logger.info("All nodes stopped")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    logger.info("\nReceived interrupt signal")
    simulator.stop_all_nodes()
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start simulator
    simulator = NodeSimulator(num_nodes=10, zones=2)
    simulator.start_all_nodes()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        simulator.stop_all_nodes()