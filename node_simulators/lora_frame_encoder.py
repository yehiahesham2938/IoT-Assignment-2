import struct
import logging

logger = logging.getLogger(__name__)

class LoRaFrameEncoder:
    """
    Encodes sensor telemetry into LoRa uplink frames.
    Uses a compact binary format to simulate real LoRa constraints.
    """
    
    FPORT = 10  # LoRa Frame Port for telemetry
    
    @staticmethod
    def encode_telemetry(telemetry_dict):
        """
        Encode telemetry to LoRa frame (42 bytes max for Class A).
        
        Binary format:
        - Bytes 0-3: Temperature (float32)
        - Bytes 4-7: Humidity (float32)
        - Bytes 8-11: Leaf Wetness (float32)
        - Bytes 12-15: Rainfall (float32)
        - Bytes 16-17: Battery Level (uint16, 0-100)
        
        Args:
            telemetry_dict: Dictionary with sensor readings
        
        Returns:
            bytes: LoRa frame payload
        """
        try:
            temp = float(telemetry_dict['temperature'])
            humidity = float(telemetry_dict['humidity'])
            leaf_wetness = float(telemetry_dict['leaf_wetness'])
            rainfall = float(telemetry_dict['rainfall'])
            battery = int(telemetry_dict.get('battery_level', 100))
            
            # Pack as binary
            frame = struct.pack(
                '<ffff',  # Little-endian: 4 floats
                temp,
                humidity,
                leaf_wetness,
                rainfall
            )
            frame += struct.pack('<H', battery)
            
            logger.debug(f"Encoded frame: {frame.hex()}")
            return frame
        
        except Exception as e:
            logger.error(f"Frame encoding error: {e}")
            return b''
    
    @staticmethod
    def decode_telemetry(frame_bytes):
        """
        Decode LoRa frame back to telemetry (for verification).
        
        Args:
            frame_bytes: Encoded frame
        
        Returns:
            dict: Decoded telemetry
        """
        try:
            if len(frame_bytes) < 18:
                raise ValueError(f"Frame too short: {len(frame_bytes)} bytes")
            
            temp, humidity, leaf_wetness, rainfall, battery = struct.unpack(
                '<ffffH',
                frame_bytes[:18]
            )
            
            return {
                'temperature': temp,
                'humidity': humidity,
                'leaf_wetness': leaf_wetness,
                'rainfall': rainfall,
                'battery_level': battery
            }
        
        except Exception as e:
            logger.error(f"Frame decoding error: {e}")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Test encoding/decoding
    test_data = {
        'temperature': 22.5,
        'humidity': 75.3,
        'leaf_wetness': 4.2,
        'rainfall': 2.1,
        'battery_level': 92
    }
    
    encoder = LoRaFrameEncoder()
    encoded = encoder.encode_telemetry(test_data)
    print(f"Encoded: {encoded.hex()}")
    
    decoded = encoder.decode_telemetry(encoded)
    print(f"Decoded: {decoded}")