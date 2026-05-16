
import struct
import base64
from cryptography.hazmat.primitives.cmac import CMAC
from cryptography.hazmat.primitives.ciphers import algorithms

def aes128_cmac(key, msg):
    """Calculate AES128-CMAC."""
    c = CMAC(algorithms.AES(key))
    c.update(msg)
    return c.finalize()

def encrypt_payload(key, dev_addr, f_cnt, payload):
    """
    Encrypt/Decrypt LoRaWAN payload using AES-128 in CTR-like mode (IEEE 802.15.4).
    """
    if isinstance(dev_addr, str):
        dev_addr = bytes.fromhex(dev_addr)
    if isinstance(key, str):
        key = bytes.fromhex(key)
        
    k = len(payload) // 16 + (1 if len(payload) % 16 != 0 else 0)
    S = b""
    for i in range(1, k + 1):
        Ai = struct.pack('<B4sB4sB', 0x01, b'\x00\x00\x00\x00', 0x00, dev_addr[::-1], f_cnt & 0xFF)
        # Ai is actually 16 bytes: 0x01 | 0x00*4 | Dir(0x00) | DevAddr(4) | FCnt(4) | 0x00 | i(1)
        # We simplify here for the simulation
        Ai = b'\x01\x00\x00\x00\x00\x00' + dev_addr[::-1] + struct.pack('<I', f_cnt) + b'\x00' + struct.pack('<B', i)
        
        from cryptography.hazmat.primitives.ciphers import Cipher, modes
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        encryptor = cipher.encryptor()
        Si = encryptor.update(Ai) + encryptor.finalize()
        S += Si
        
    res = bytes([p ^ s for p, s in zip(payload, S)])
    return res

def calculate_mic(key, msg, dev_addr, f_cnt, dir=0):
    """Calculate LoRaWAN MIC."""
    if isinstance(dev_addr, str):
        dev_addr = bytes.fromhex(dev_addr)
    if isinstance(key, str):
        key = bytes.fromhex(key)
        
    # B0 block
    b0 = struct.pack('<B4sB4sIBB', 0x49, b'\x00\x00\x00\x00', dir, dev_addr[::-1], f_cnt, 0x00, len(msg))
    
    cmac = aes128_cmac(key, b0 + msg)
    return cmac[:4]

def build_abp_packet(dev_addr, nwk_skey, app_skey, f_cnt, f_port, payload_bytes):
    """Build a complete LoRaWAN ABP Uplink packet."""
    # 1. Encrypt payload
    enc_payload = encrypt_payload(bytes.fromhex(app_skey), dev_addr, f_cnt, payload_bytes)
    
    # 2. Build MHDR (Unconfirmed Uplink = 0x40)
    mhdr = b'\x40'
    
    # 3. Build FHDR (DevAddr | FCtrl | FCnt | FOpts)
    dev_addr_bytes = bytes.fromhex(dev_addr)[::-1] # Little endian
    fhdr = dev_addr_bytes + b'\x00' + struct.pack('<H', f_cnt & 0xFFFF)
    
    # 4. Assemble message for MIC calculation
    msg = mhdr + fhdr + struct.pack('<B', f_port) + enc_payload
    
    # 5. Calculate MIC
    mic = calculate_mic(bytes.fromhex(nwk_skey), msg, dev_addr, f_cnt)
    
    # 6. Final packet
    packet = msg + mic
    return base64.b64encode(packet).decode()
