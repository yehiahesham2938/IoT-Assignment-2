import json
import random
import time
from datetime import datetime, timedelta
import logging
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SensorNode:
    """
    Simulates a LoRaWAN crop sensor node.
    Measures: Temperature, Humidity, Leaf Wetness, Rainfall
    """
    
    def __init__(self, node_id, zone, gateway_id):
        """
        Initialize sensor node.
        
        Args:
            node_id: Unique node identifier (1-10)
            zone: Zone number (1 or 2)
            gateway_id: Associated gateway identifier
        """
        self.node_id = node_id
        self.zone = zone
        self.gateway_id = gateway_id
        from config import get_device_credentials
        creds = get_device_credentials(node_id, zone)
        self.device_eui = creds['dev_eui']
        
        # Sensor state tracking
        self.temperature = 20.0  # Initial temp in Celsius
        self.humidity = 65.0     # Initial humidity in %
        self.leaf_wetness = 0.0  # Initial leaf wetness in hours
        self.rainfall = 0.0      # Rainfall in mm
        
        # Simulation state
        self.last_update = datetime.now()
        self.transmission_interval = 300  # 5 minutes in seconds
        self.rainfall_event_active = False
        self.rainfall_accumulation_time = 0
        
        logger.info(f"Node {self.node_id} (Zone {self.zone}) initialized")
    
    def generate_telemetry(self):
        """
        Generate realistic telemetry data with environmental patterns.
        
        Returns:
            dict: Telemetry payload with sensor readings
        """
        current_time = datetime.now()
        
        # Simulate temperature variation (daily cycle: 15-28°C)
        hour = current_time.hour
        base_temp = 15 + 13 * (1 + math.sin((hour - 6) * math.pi / 12)) / 2
        self.temperature = base_temp + random.uniform(-2, 2)
        
        # Simulate humidity buildup (gradual increase for disease simulation)
        if random.random() < 0.3:  # 30% chance of humidity increase
            self.humidity = min(self.humidity + random.uniform(1, 5), 95)
        else:
            self.humidity = max(self.humidity - random.uniform(0.5, 2), 40)
        
        # Simulate leaf wetness (increases after rain/humidity)
        if self.humidity > 80:
            self.leaf_wetness = min(self.leaf_wetness + random.uniform(0.5, 1.5), 12)
        else:
            self.leaf_wetness = max(self.leaf_wetness - random.uniform(0.3, 0.8), 0)
        
        # Simulate rainfall events (occasional heavy rain)
        if random.random() < 0.05:  # 5% chance of rainfall event
            self.rainfall_event_active = True
            self.rainfall_accumulation_time = 0
        
        if self.rainfall_event_active:
            self.rainfall += random.uniform(2, 8)
            self.rainfall_accumulation_time += 5
            if self.rainfall_accumulation_time > 20:  # Event duration ~20 min
                self.rainfall_event_active = False
                self.rainfall = 0
        
        # Create telemetry payload
        payload = {
            'node_id': self.node_id,
            'zone': self.zone,
            'device_eui': self.device_eui,
            'timestamp': current_time.isoformat(),
            'temperature': round(self.temperature, 2),
            'humidity': round(self.humidity, 2),
            'leaf_wetness': round(self.leaf_wetness, 2),
            'rainfall': round(self.rainfall, 2),
            'battery_level': random.uniform(85, 100)
        }
        
        logger.info(f"Node {self.node_id}: T={self.temperature:.1f}°C, "
                   f"H={self.humidity:.1f}%, LW={self.leaf_wetness:.1f}h, RF={self.rainfall:.1f}mm")
        
        return payload
    
    def get_transmission_interval(self):
        """Returns transmission interval in seconds."""
        return self.transmission_interval


if __name__ == "__main__":
    import math
    
    # Test the sensor node
    node = SensorNode(node_id=1, zone=1, gateway_id="0000000000000001")
    
    # Simulate 10 telemetry readings
    for i in range(10):
        telemetry = node.generate_telemetry()
        print(json.dumps(telemetry, indent=2))
        time.sleep(1)