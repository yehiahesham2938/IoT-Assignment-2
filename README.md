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
├── chirpstack_config/ # ChirpStack Docker setup
├── node_simulators/ # LoRaWAN node simulators
├── bridge_scripts/ # ChirpStack to AWS bridge
├── ota_handler/ # OTA update handler
├── aws_infrastructure/ # AWS CloudFormation/Terraform
├── security/ # Security utilities
├── tests/ # Test scripts
├── documentation/ # Technical documentation
└── demo_data/ # Sample telemetry data