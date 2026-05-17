import os
import logging
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

def generate_device_certificates(device_id, days_valid=365):
    """
    Generate self-signed certificate for a device using cryptography library.
    """
    cert_dir = f"../certificates/{device_id}"
    os.makedirs(cert_dir, exist_ok=True)
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, device_id),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=days_valid)
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    # Save private key
    key_file = os.path.join(cert_dir, 'private.key')
    with open(key_file, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Save certificate
    cert_file = os.path.join(cert_dir, 'certificate.pem')
    with open(cert_file, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    logger.info(f"Generated certificates for {device_id}")


if __name__ == "__main__":
    for i in range(1, 11):
        device_name = f"SensorNode_{i:02d}"
        generate_device_certificates(device_name)
        print(f"✓ Generated {device_name}")
