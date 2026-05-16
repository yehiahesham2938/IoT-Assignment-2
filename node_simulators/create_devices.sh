#!/bin/bash
# Create remaining 9 devices in ChirpStack database
# This script directly inserts devices into PostgreSQL for the 10-node simulator

POSTGRES_HOST="localhost"
POSTGRES_PORT="5435"
POSTGRES_USER="chirpstack"
POSTGRES_PASSWORD="chirpstack"
POSTGRES_DB="chirpstack"
TENANT_ID="30a9ed7c-2f02-4699-9d02-a3fa72f7f56f"
APPLICATION_ID="958773be-569a-447d-bd73-1f6b63682bc7"
DEVICE_PROFILE_ID="f11bb2da-dd5e-4fd5-86a5-85fe26b2b8dc"

# Device 1 already created via UI, create devices 2-10
for node_num in {2..10}; do
    zone=$(( (node_num - 1) / 5 + 1 ))
    device_name="SensorNode_$(printf "%02d" $node_num)"
    device_eui="70b3d501$(printf "%08x" $node_num)"
    device_id=$(uuidgen)
    
    echo "Creating $device_name (Zone $zone, DevEUI: $device_eui)..."
    
    # SQL to insert device
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
INSERT INTO device (
    id, application_id, device_profile_id, name, description, dev_eui,
    device_status_battery, device_status_margin, device_status_external_altitude,
    skip_fcnt_check, is_disabled, last_seen_at, created_at, updated_at
) VALUES (
    '$(echo -n "$device_id" | cut -c1-36)',
    '$(echo -n "$APPLICATION_ID" | cut -c1-36)',
    '$(echo -n "$DEVICE_PROFILE_ID" | cut -c1-36)',
    '$device_name',
    'Crop sensor node $node_num (Zone $zone)',
    E'\\x$device_eui'::bytea,
    100,
    10,
    0,
    false,
    false,
    NOW(),
    NOW(),
    NOW()
) ON CONFLICT (dev_eui) DO NOTHING;
EOF
done

echo "Device creation complete!"
