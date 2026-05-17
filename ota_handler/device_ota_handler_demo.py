import json
import logging
import time
import threading
from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeviceOTAHandler:
    """
    Simulated device-side OTA update handler.
    Subscribes to AWS IoT Jobs, applies updates, and reports status.
    """
    
    def __init__(self, device_id, aws_endpoint, cert_path, key_path, ca_path):
        """
        Initialize OTA handler.
        
        Args:
            device_id: Device name (e.g., 'SensorNode_06')
            aws_endpoint: AWS IoT endpoint
            cert_path, key_path, ca_path: Certificate paths
        """
        self.device_id = device_id
        self.aws_endpoint = aws_endpoint
        self.mqtt_client = AWSIoTMQTTClient(device_id)
        self.mqtt_client.configureEndpoint(aws_endpoint, 8883)
        self.mqtt_client.configureCredentials(ca_path, key_path, cert_path)
        self.mqtt_client.configureConnectDisconnectTimeout(10)
        self.mqtt_client.configureMQTTOperationTimeout(5)
        
        # Current thresholds
        self.current_thresholds = {
            "moderate_humidity_min": 70,
            "moderate_humidity_max": 85,
            "moderate_temp_min": 15,
            "moderate_temp_max": 25,
            "high_humidity": 85,
            "high_temp_min": 18,
            "high_temp_max": 25,
            "critical_leaf_wetness": 8,
            "critical_rainfall": 5
        }
        
        self.previous_thresholds = None
        self.connected = False
    
    def connect(self):
        """Connect to AWS IoT Core."""
        try:
            self.mqtt_client.connect()
            self.connected = True
            logger.info(f"Device {self.device_id} connected to AWS IoT")
            
            # Subscribe to job topics
            self._subscribe_to_jobs()
            
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from AWS IoT."""
        if self.connected:
            self.mqtt_client.disconnect()
            self.connected = False
    
    def _subscribe_to_jobs(self):
        """Subscribe to AWS IoT Jobs topics."""
        job_topic = f"$aws/things/{self.device_id}/jobs/notify"
        
        try:
            self.mqtt_client.subscribe(job_topic, 1, self._on_job_message)
            logger.info(f"Subscribed to {job_topic}")
        except Exception as e:
            logger.error(f"Subscription failed: {e}")
    
    def _on_job_message(self, client, userdata, message):
        """Handle incoming job notification."""
        try:
            logger.info(f"Job notification received on {message.topic}")
            payload = json.loads(message.payload.decode())
            
            job_id = payload.get('jobs', {}).get('queued', [{}])[0].get('jobId')
            if job_id:
                self._process_job(job_id)
        
        except Exception as e:
            logger.error(f"Job message error: {e}")
    
    def _process_job(self, job_id):
        """Process a job: download, apply, report status."""
        logger.info(f"Processing job {job_id}...")
        
        # Step 1: Report IN_PROGRESS
        self._report_job_status(job_id, 'IN_PROGRESS', 'Started update')
        time.sleep(2)
        
        # Step 2: Simulate download and validation
        logger.info(f"Downloading update for job {job_id}")
        time.sleep(3)
        
        # Step 3: Get job document
        try:
            # In real scenario, would fetch from $aws/things/{thing}/jobs/{jobId}
            # For simulation, assume success
            
            # Step 4: Apply update
            logger.info("Applying new thresholds...")
            self._apply_update()
            time.sleep(2)
            
            # Step 5: Verify update
            logger.info("Verifying update...")
            time.sleep(1)
            
            # Step 6: Report SUCCESS
            self._report_job_status(job_id, 'SUCCEEDED', 'Thresholds updated successfully')
        
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self._report_job_status(job_id, 'FAILED', str(e))
    
    def _apply_update(self):
        """Apply new thresholds."""
        # Save previous thresholds for rollback
        self.previous_thresholds = self.current_thresholds.copy()
        
        # Apply new thresholds (simulated from OTA document)
        self.current_thresholds.update({
            "moderate_humidity_max": 80,
            "moderate_temp_min": 16,
            "high_humidity": 80,
            "critical_leaf_wetness": 6,
            "critical_rainfall": 4
        })
        
        logger.info(f"Thresholds updated: {self.current_thresholds}")
    
    def _report_job_status(self, job_id, status, message):
        """Report job status to AWS IoT Core."""
        try:
            status_topic = f"$aws/things/{self.device_id}/jobs/{job_id}/update"
            
            payload = {
                'status': status,
                'statusDetails': {
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            self.mqtt_client.publish(status_topic, json.dumps(payload), 1)
            logger.info(f"Reported job status: {status}")
        
        except Exception as e:
            logger.error(f"Status report failed: {e}")
    
    def rollback(self):
        """Rollback to previous thresholds."""
        if self.previous_thresholds:
            self.current_thresholds = self.previous_thresholds.copy()
            self.previous_thresholds = None
            logger.info("Rolled back to previous thresholds")


if __name__ == "__main__":
    import sys
    
    device_id = sys.argv[1] if len(sys.argv) > 1 else 'SensorNode_06'
    aws_endpoint = 'YOUR_ENDPOINT.iot.REGION.amazonaws.com'
    
    handler = DeviceOTAHandler(device_id, aws_endpoint, 
                               f'../certificates/{device_id}/cert.pem',
                               f'../certificates/{device_id}/key.pem',
                               f'../certificates/{device_id}/ca.pem')
    
    if handler.connect():
        try:
            logger.info(f"OTA handler ready for {device_id}")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            handler.disconnect()
    else:
        logger.error("Failed to connect")
