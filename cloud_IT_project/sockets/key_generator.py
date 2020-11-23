from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def generate_keys():
    # generate private/public key pair
    keys = rsa.generate_private_key(backend = default_backend(), public_exponent = 65537, \
        key_size = 2048)
    public_key = generate_pub_key(keys)
    private_key = generate_pri_key(keys)

def generate_pub_key(keys):
    # get public key in OpenSSH format
    public_key = keys.public_key().public_bytes(serialization.Encoding.OpenSSH, \
        serialization.PublicFormat.OpenSSH)
    public_key_to_str = public_key.decode('utf-8')
    # return public_key_to_str
    print('Public key = ')
    print(public_key_to_str)

def generate_pri_key(keys):
    # get private key in PEM container format
    pem_format = keys.private_bytes(encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm = serialization.NoEncryption())
    private_key_to_str = pem_format.decode('utf-8')
    # return private_key_to_str
    print('Private key = ')
    print(private_key_to_str)

print(generate_keys())