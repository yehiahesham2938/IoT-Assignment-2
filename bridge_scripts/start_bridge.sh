#!/bin/bash
source .env
python3 chirpstack_aws_bridge.py \
    --chirpstack-host $CHIRPSTACK_HOST \
    --aws-endpoint $AWS_ENDPOINT \
    --cert $CERT_PATH \
    --key $KEY_PATH \
    --ca $CA_PATH
