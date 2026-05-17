# Crop Disease Early Warning Network - IoT Assignment 2

## Project Overview
This project implements a distributed IoT network for early detection of crop fungal diseases using LoRaWAN sensors, AWS IoT Core, and machine learning-based risk assessment.

### Key Components
- **LoRaWAN Network:** ChirpStack with 10 simulated sensor nodes
- **AWS IoT Core:** MQTT broker and device management
- **Disease Risk Engine:** Real-time risk scoring algorithm
- **OTA Updates:** Firmware updates via AWS IoT Jobs
- **Security:** X.509 certificates, TLS encryption, least-privilege policies

## Project Structure
```
.
├── chirpstack_config/              # ChirpStack Docker setup & configuration
├── node_simulators/                # LoRaWAN node simulators
│   ├── run_simulator.py           # Main sensor simulator (10 nodes, 5-min interval)
│   ├── sensor_node_base.py        # Realistic data generation
│   ├── config.py                  # Device credentials & configuration
│   └── create_devices.sh           # ChirpStack device setup
├── bridge_scripts/                 # ChirpStack to AWS bridge
│   └── chirpstack_aws_bridge.py   # MQTT topic forwarding
├── ota_handler/                    # OTA update handler
│   └── device_ota_handler.py      # AWS IoT Jobs processing
├── security/                       # Security utilities
│   ├── generate_certificates.py   # X.509 certificate generation
│   ├── rogue_device_simulator.py  # Security testing
│   └── certificates/               # Generated device certificates
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── IoT_Assignment_2_Technical_Report.md  # Complete technical documentation
```

---

## Prerequisites

### System Requirements
- **Python:** 3.8 or higher
- **Docker & Docker Compose:** Latest version (for ChirpStack)
- **Git:** For version control
- **AWS Account:** With IoT Core permissions

### Required Python Packages
See [requirements.txt](requirements.txt) for full list:
- `paho-mqtt` - MQTT client
- `cryptography` - X.509 certificate generation
- `boto3` - AWS SDK
- `python-dotenv` - Environment variables

### AWS Setup Requirements
1. **AWS IoT Core:**
   - IoT endpoint (format: `xxxxxxxx.iot.region.amazonaws.com`)
   - Thing Groups: `Zone_1`, `Zone_2`
   - Things: `SensorNode_01` through `SensorNode_10`
   - Certificates: X.509 certificates attached to each Thing
   - Policies: Zone-based access control policies

2. **AWS CloudWatch:**
   - Log groups for Lambda functions
   - Alarms for critical events

3. **AWS S3:**
   - OTA firmware bucket (`crop-firmware-bucket`)
   - OTA updates bucket (`crop-ota-updates`)

---

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/yehiahesham2938/IoT-Assignment-2.git
cd IoT-Assignment-2
```

### 2. Install Python Dependencies
```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure ChirpStack

#### Start ChirpStack Services
```bash
cd chirpstack_config
docker-compose up -d
```

**Verify ChirpStack is running:**
```bash
# ChirpStack Web UI: http://localhost:8081
# Default credentials: admin/admin
# PostgreSQL: localhost:5435
# Redis: localhost:6379
# MQTT Broker: localhost:1883
```

#### Create ChirpStack Devices
```bash
# Option 1: Run the setup script
bash create_devices.sh

# Option 2: Manual setup in Web UI
# 1. Create new application "CropMonitor"
# 2. Create 10 devices: SensorNode_01 through SensorNode_10
# 3. Copy DevEUI and AppKey for each device to config.py
```

### 4. AWS IoT Configuration

#### Create Things and Thing Groups
```bash
# Create Thing Groups
aws iot create-thing-group --thing-group-name Zone_1
aws iot create-thing-group --thing-group-name Zone_2

# Create Things
for i in {01..05}; do
  aws iot create-thing --thing-name SensorNode_$i
  aws iot add-thing-to-thing-group --thing-name SensorNode_$i --thing-group-name Zone_1
done

for i in {06..10}; do
  aws iot create-thing --thing-name SensorNode_$i
  aws iot add-thing-to-thing-group --thing-name SensorNode_$i --thing-group-name Zone_2
done
```

#### Generate X.509 Certificates
```bash
cd security
python generate_certificates.py

# Output: 10 directories under certificates/{device_id}/
# Each containing: private.key, certificate.pem
```

#### Attach Certificates to Things
```bash
# For each device, attach the certificate from certificates/{device_id}/certificate.pem
# Use AWS IoT console or AWS CLI:
aws iot attach-thing-principal \
  --thing-name SensorNode_01 \
  --principal arn:aws:iot:REGION:ACCOUNT:cert/CERT_ID
```

#### Create IoT Policies
```bash
# Create Zone_1_Policy and Zone_2_Policy
# Zone policies restrict cross-zone communication
# See IoT_Assignment_2_Technical_Report.md Section 3 for policy JSON
aws iot create-policy --policy-name Zone_1_Policy --policy-document file://zone_1_policy.json
aws iot create-policy --policy-name Zone_2_Policy --policy-document file://zone_2_policy.json

# Attach policies to certificates
aws iot attach-policy --policy-name Zone_1_Policy --target arn:aws:iot:REGION:ACCOUNT:cert/CERT_ID
```

#### Get AWS IoT Endpoint
```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS
# Example: a19awyw8hpyek5-ats.iot.eu-north-1.amazonaws.com
```

### 5. Update Configuration Files

#### node_simulators/config.py
Update with your AWS IoT credentials:
```python
AWS_IOT_ENDPOINT = "your-endpoint.iot.region.amazonaws.com"
AWS_IOT_PORT = 8883
REGION = "eu-north-1"

DEVICES = {
    "SensorNode_01": {
        "device_eui": "70b3d501xxxxxxxx",
        "app_key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    },
    # ... other devices
}
```

#### Security Files
Place your AWS certificates in the appropriate location:
```bash
# Copy Amazon Root CA 4 certificate
aws iot get-registration-code > certificates/root-ca.pem

# Verify certificate structure
ls -la certificates/SensorNode_01/
# Should contain: private.key, certificate.pem
```

---

## Execution Instructions

### Running the Complete System

#### Step 1: Start ChirpStack Services
```bash
cd chirpstack_config
docker-compose up -d

# Verify all services are healthy
docker-compose ps
# All containers should show "Up"
```

#### Step 2: Verify ChirpStack Dashboard
Open browser: **http://localhost:8081**
- Login: admin/admin
- Verify 10 devices are registered and ACTIVE
- Check gateways (Gateway_01, Gateway_02) are connected

#### Step 3: Generate Device Certificates
```bash
cd security
python generate_certificates.py

# Verify output
# ✓ Generated SensorNode_01
# ✓ Generated SensorNode_02
# ... (all 10 devices)
```

#### Step 4: Start Sensor Simulator
```bash
cd node_simulators
python run_simulator.py

# Expected output:
# [INFO] 10 devices initialized
# [INFO] Zone_1: SensorNode_01-05
# [INFO] Zone_2: SensorNode_06-10
# [INFO] Starting 5-minute telemetry cycle
# [INFO] SensorNode_01: Temp=22.5°C, Humidity=65.2%, LeafWetness=0.0h, Rainfall=0.0mm
# ... (continues every 5 minutes)
```

#### Step 5: Start Bridge (in separate terminal)
```bash
cd bridge_scripts
python chirpstack_aws_bridge.py

# Expected output:
# [INFO] Connected to ChirpStack MQTT Broker (localhost:1883)
# [INFO] Connected to AWS IoT Core (endpoint:8883)
# [INFO] Bridge running - forwarding messages...
# [INFO] [Zone_1] Received from SensorNode_01 -> Forwarding to AWS
# [INFO] [Zone_2] Received from SensorNode_06 -> Forwarding to AWS
```

#### Step 6: Start OTA Handler (in separate terminal)
```bash
cd ota_handler
python device_ota_handler.py SensorNode_06

# Expected output:
# [INFO] Device OTA Handler for SensorNode_06 started
# [INFO] Connected to AWS IoT Core
# [INFO] Subscribed to job topics
# [INFO] Waiting for OTA jobs...
# (Waits for OTA job assignment)
```

---

### Individual Component Execution

#### A. LoRaWAN Sensor Simulator Only
```bash
cd node_simulators
python run_simulator.py

# Simulates 10 sensor nodes transmitting every 5 minutes
# Data includes: Temperature, Humidity, Leaf Wetness, Rainfall
# Realistic patterns: Daily cycles, humidity buildup, rainfall events
```

#### B. Generate Device Certificates Only
```bash
cd security
python generate_certificates.py

# Generates X.509 RSA 2048-bit certificates for all 10 devices
# Output location: certificates/{device_id}/
# Files: private.key, certificate.pem (PEM format)
```

#### C. Security Testing - Rogue Device Rejection
```bash
cd security
python rogue_device_simulator.py

# Attempts connection without valid certificate
# Expected: ❌ Connection REJECTED - No valid certificates provided
# Demonstrates AWS IoT Core rejecting unauthorized devices
```

#### D. Bridge ChirpStack to AWS Only
```bash
cd bridge_scripts
python chirpstack_aws_bridge.py

# Forwards messages from ChirpStack MQTT to AWS IoT Core
# Topic mapping: dt/zone{1|2}/sensor_data
# Requires ChirpStack running (see Step 1)
```

#### E. OTA Update Handler for Single Device
```bash
cd ota_handler
python device_ota_handler.py SensorNode_06

# Listens for AWS IoT Jobs and applies OTA updates
# Simulates firmware download, verification, application
# Reports status: QUEUED → IN_PROGRESS → SUCCEEDED/FAILED
```

---

## Testing Instructions

### Unit Tests (If Available)
```bash
cd tests
python -m pytest test_*.py -v
```

### Integration Testing

#### 1. Test ChirpStack Connectivity
```bash
# From node_simulators directory
python test_api.py

# Should show successful device registration
```

#### 2. Test AWS IoT Connectivity
```bash
# Test certificate validity
openssl verify -CAfile certificates/root-ca.pem certificates/SensorNode_01/certificate.pem
# Output: "OK"

# Test MQTT connection
mosquitto_sub -h your-endpoint.iot.region.amazonaws.com \
  -p 8883 \
  --cert certificates/SensorNode_01/certificate.pem \
  --key certificates/SensorNode_01/private.key \
  --cafile certificates/root-ca.pem \
  -t 'dt/zone1/#' \
  --tls-version tlsv1.2

# Should show incoming messages from simulator
```

#### 3. Test Data Flow (End-to-End)
```bash
# Terminal 1: Start ChirpStack
cd chirpstack_config && docker-compose up -d

# Terminal 2: Start simulator
cd node_simulators && python run_simulator.py

# Terminal 3: Start bridge
cd bridge_scripts && python chirpstack_aws_bridge.py

# Terminal 4: Monitor AWS messages
mosquitto_sub -h your-endpoint.iot.region.amazonaws.com \
  -p 8883 \
  --cert certificates/SensorNode_01/certificate.pem \
  --key certificates/SensorNode_01/private.key \
  --cafile certificates/root-ca.pem \
  -t 'dt/#' -v

# Should see sensor data every 5 minutes
```

#### 4. Test OTA Updates
```bash
# Create OTA job in AWS IoT console
# Target: Zone_2 (SensorNode_06-10)
# Job document: Firmware update + threshold changes

# Terminal: Run OTA handler
cd ota_handler && python device_ota_handler.py SensorNode_06

# Monitor job execution in AWS console
# Should see: QUEUED → IN_PROGRESS → SUCCEEDED
```

#### 5. Test Rollback Mechanism
```bash
# Create OTA job with intentional failures
# Monitor CloudWatch logs for:
# - Device failures (2+ devices)
# - Automatic rollback trigger
# - Device recovery to previous version
```

---

## Configuration Details

### Device Configuration (config.py)
```python
# 10 Sensor nodes across 2 zones
ZONE_1_DEVICES = ["SensorNode_01", "SensorNode_02", "SensorNode_03", "SensorNode_04", "SensorNode_05"]
ZONE_2_DEVICES = ["SensorNode_06", "SensorNode_07", "SensorNode_08", "SensorNode_09", "SensorNode_10"]

# Transmission interval: 5 minutes (300 seconds)
TRANSMISSION_INTERVAL = 300

# Device EUI format (unique per device)
DEVICE_EUI_TEMPLATE = "70b3d501{node_id:08x}"
```

### Telemetry Data Parameters
```python
# Temperature: 15-30°C with daily sinusoidal variation
TEMP_MIN = 15.0
TEMP_MAX = 30.0
TEMP_OFFSET = 22.5
TEMP_AMPLITUDE = 7.5

# Humidity: 30-95% with gradual buildup
HUMIDITY_MIN = 30
HUMIDITY_MAX = 95
HUMIDITY_BASE = 60
HUMIDITY_AMPLITUDE = 30

# Leaf Wetness: 0-12 hours (correlates with humidity)
LEAF_WETNESS_MAX = 12.0

# Rainfall: 0-8 mm per 5-minute interval
RAINFALL_MAX = 8.0
RAINFALL_PROBABILITY = 0.05  # ~5% chance per cycle
```

### AWS IoT Configuration
```python
# Endpoint format
AWS_IOT_ENDPOINT = "{account-specific}.iot.{region}.amazonaws.com"
AWS_IOT_PORT = 8883
AWS_IOT_PROTOCOL = "MQTT with TLS 1.2"

# Thing Groups
THING_GROUPS = ["Zone_1", "Zone_2"]

# Certificate paths
CERT_PATH = "certificates/{device_id}/certificate.pem"
KEY_PATH = "certificates/{device_id}/private.key"
CA_PATH = "certificates/AmazonRootCA4.pem"

# MQTT Topics
ZONE_1_TOPIC = "dt/zone1/sensor_data"
ZONE_2_TOPIC = "dt/zone2/sensor_data"
```

---

## Disease Risk Engine

### Risk Levels and Thresholds

| Risk Level | Temperature | Humidity | Leaf Wetness | Rainfall | Action |
|-----------|-------------|----------|--------------|----------|--------|
| **LOW** | <15°C or >35°C | Any | Any | Any | No action |
| **MODERATE** | 15-35°C | 70-84% | <6 hours | <5mm | Advisory alert |
| **HIGH** | 18-25°C | ≥85% | 6-8 hours | <5mm | Urgent alert + spray |
| **CRITICAL** | 18-25°C | ≥85% | >8 hours | >5mm | Emergency response |

### Risk Calculation Example
```python
def calculate_risk(temperature, humidity, leaf_wetness, rainfall):
    if temperature < 15 or temperature > 35:
        return "LOW"
    elif humidity < 70:
        return "LOW"
    elif humidity >= 85 and leaf_wetness >= 6:
        if 18 <= temperature <= 25:
            if rainfall > 5:
                return "CRITICAL"
            else:
                return "HIGH"
    return "MODERATE"
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. ChirpStack Won't Start
```bash
# Check Docker is running
docker ps

# Check Docker Compose syntax
cd chirpstack_config
docker-compose config

# View logs
docker-compose logs chirpstack

# Solution: Ensure ports 5435, 6379, 8081, 1883 are free
```

#### 2. MQTT Connection Failed
```bash
# Verify ChirpStack MQTT broker is running
docker-compose logs mosquitto

# Test MQTT connectivity
mosquitto_pub -h localhost -p 1883 -t test -m "hello"
mosquitto_sub -h localhost -p 1883 -t test

# Check firewall rules
```

#### 3. AWS Certificate Errors
```bash
# Verify certificate format
openssl x509 -in certificates/SensorNode_01/certificate.pem -text -noout

# Check certificate validity
openssl verify -CAfile certificates/root-ca.pem certificates/SensorNode_01/certificate.pem

# Ensure certificate is attached to Thing
aws iot describe-thing --thing-name SensorNode_01
```

#### 4. Bridge Not Forwarding Messages
```bash
# Check ChirpStack topics
mosquitto_sub -h localhost -p 1883 -t '#' -v

# Verify AWS credentials
aws sts get-identity

# Check CloudWatch logs for errors
```

#### 5. OTA Job Stuck in QUEUED
```bash
# Verify device is connected
aws iot describe-thing-attribute --thing-name SensorNode_06

# Check job document format
aws iot describe-job --job-id CropThresholdUpdateJob

# Monitor device handler logs for errors
```

---

## Documentation

For detailed technical information, see:
- **[IoT_Assignment_2_Technical_Report.md](IoT_Assignment_2_Technical_Report.md)** - Complete 10-page technical documentation
  - System architecture
  - LoRaWAN simulation details
  - AWS IoT Core setup
  - Disease risk engine algorithm
  - OTA update workflow
  - Security implementation
  - Screenshots and diagrams

---

## API Reference

### run_simulator.py
```python
# Start simulator with custom interval
simulator = LoRaSimulator(transmission_interval=300)  # 5 minutes
simulator.start()
simulator.add_device("SensorNode_01", zone="Zone_1")
simulator.add_device("SensorNode_02", zone="Zone_1")
# ... add all 10 devices
simulator.run()
```

### device_ota_handler.py
```python
# Start OTA handler for specific device
ota_handler = OTAHandler("SensorNode_06")
ota_handler.connect()
ota_handler.subscribe_to_jobs()
ota_handler.handle_job_updates()  # Blocking
```

### chirpstack_aws_bridge.py
```python
# Start message bridge
bridge = ChirpStackAWSBridge()
bridge.connect_to_chirpstack("localhost", 1883)
bridge.connect_to_aws_iot("your-endpoint.iot.region.amazonaws.com")
bridge.forward_messages()  # Blocking
```

---

## Performance Metrics

- **Sensor Nodes:** 10 devices
- **Transmission Interval:** 5 minutes (300 seconds)
- **Message Frequency:** 288 messages per device per day
- **Total Daily Messages:** 2,880 messages across all devices
- **Latency:** <1 second from sensor to ChirpStack
- **Bridge Latency:** <2 seconds from ChirpStack to AWS
- **Certificate Generation:** ~2-3 seconds for all 10 devices
- **OTA Update Time:** 5-10 minutes per device

---

## Security Considerations

✓ **X.509 Mutual TLS Authentication** - Device and server certificates  
✓ **Zone-Based Access Control** - IoT Policies prevent cross-zone communication  
✓ **AES-128-GCM Encryption** - All AWS IoT messages encrypted  
✓ **Certificate Pinning** - Devices verify server certificate chain  
✓ **Private Key Protection** - Keys stored locally, never transmitted  
✓ **Device Defender** - Audits anomalous device behavior  
✓ **Rogue Device Rejection** - Unauthorized devices cannot connect  

---

## License
See [LICENSE](LICENSE) file for details.


---

## Support & Contact
For issues, questions, or clarifications:
- Create an issue in the GitHub repository
- Review the technical documentation
- Check the troubleshooting section above