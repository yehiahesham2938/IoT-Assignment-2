"""
Device OTA Handler - Demo/Test Mode
Simulates OTA update process without requiring actual AWS IoT connection.
"""
import json
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeviceOTAHandlerDemo:
    """
    Demo version of DeviceOTAHandler for testing without AWS connection.
    """
    
    def __init__(self, device_id):
        """Initialize demo OTA handler."""
        self.device_id = device_id
        
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
        logger.info(f"Device {self.device_id} initialized")
        logger.info(f"Current thresholds: {self.current_thresholds}")
    
    def simulate_job_received(self, job_id):
        """Simulate receiving an OTA job."""
        logger.info(f"=== OTA Job Received: {job_id} ===")
        self._process_job(job_id)
    
    def _process_job(self, job_id):
        """Process a job: download, apply, report status."""
        logger.info(f"Processing job {job_id}...")
        
        # Step 1: Report IN_PROGRESS
        self._report_job_status(job_id, 'IN_PROGRESS', 'Started update')
        time.sleep(1)
        
        # Step 2: Simulate download and validation
        logger.info(f"Downloading update for job {job_id}")
        time.sleep(2)
        
        # Step 3: Get job document
        try:
            # In real scenario, would fetch from $aws/things/{thing}/jobs/{jobId}
            # For simulation, assume success
            logger.info("Job document retrieved successfully")
            
            # Step 4: Apply update
            logger.info("Applying new thresholds...")
            self._apply_update()
            time.sleep(1)
            
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
        logger.info("--- Applying Threshold Update ---")
        
        # Save previous thresholds for rollback
        self.previous_thresholds = self.current_thresholds.copy()
        logger.info(f"Backed up previous thresholds: {self.previous_thresholds}")
        
        # Apply new thresholds (simulated from OTA document)
        updates = {
            "moderate_humidity_max": 80,
            "moderate_temp_min": 16,
            "high_humidity": 80,
            "critical_leaf_wetness": 6,
            "critical_rainfall": 4
        }
        
        self.current_thresholds.update(updates)
        
        logger.info("Changes made:")
        for key, value in updates.items():
            old_value = self.previous_thresholds.get(key)
            logger.info(f"  {key}: {old_value} → {value}")
        
        logger.info(f"New thresholds: {self.current_thresholds}")
    
    def _report_job_status(self, job_id, status, message):
        """Report job status to AWS IoT Core."""
        status_data = {
            'deviceId': self.device_id,
            'jobId': job_id,
            'status': status,
            'statusDetails': {
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"--- Job Status Report ---")
        logger.info(f"Status: {status}")
        logger.info(f"Message: {message}")
        logger.info(f"Timestamp: {status_data['statusDetails']['timestamp']}")
    
    def rollback(self):
        """Rollback to previous thresholds."""
        if self.previous_thresholds:
            logger.info("--- Rolling Back Thresholds ---")
            self.current_thresholds = self.previous_thresholds.copy()
            self.previous_thresholds = None
            logger.info(f"Rolled back to: {self.current_thresholds}")
        else:
            logger.warning("No previous thresholds to rollback to")


def main():
    import sys
    
    device_id = sys.argv[1] if len(sys.argv) > 1 else 'SensorNode_06'
    
    logger.info(f"Starting Device OTA Handler Demo for {device_id}")
    logger.info("Note: This is a demo mode without actual AWS connection")
    
    handler = DeviceOTAHandlerDemo(device_id)
    
    # Simulate receiving a job
    job_id = "CropThresholdUpdateJob_001"
    logger.info(f"\nSimulating OTA job notification...")
    time.sleep(1)
    
    handler.simulate_job_received(job_id)
    
    logger.info("\n=== OTA Update Demonstration Complete ===")
    logger.info(f"Device: {device_id}")
    logger.info(f"Final Thresholds: {handler.current_thresholds}")


if __name__ == "__main__":
    main()
