from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Hash import SHA512, SHA384, SHA256, SHA, MD5
from Cryptodome import Random
from base64 import b64encode, b64decode
import rsa

hash_type = "SHA-256"


def newkeys(keysize):
    random_generator = Random.new().read
    key = RSA.generate(keysize, random_generator)
    private, public = key, key.publickey()
    return public, private


def importKey(externKey):
    return RSA.importKey(externKey)


def exportKey(internKey):
    return internKey.exportKey("DER")


def getpublickey(priv_key):
    return priv_key.publickey()


def encrypt(message, pub_key):
    # RSA encryption protocol according to PKCS#1 OAEP
    #key = importKey(pub_key)
    cipher = PKCS1_OAEP.new(pub_key)
    # print("\n encrypt pub_key" + str(pub_key))#debugging
    return cipher.encrypt(message)


def decrypt(ciphertext, priv_key):
    # RSA encryption protocol according to PKCS#1 OAEP
    cipher = PKCS1_OAEP.new(priv_key)
    message = cipher.decrypt(ciphertext)
    # print("\n decrypt priv_key" + str(priv_key))#debugging
    return message


def sign(message, priv_key, hashAlg="SHA-256"):
    global hash_type
    hash_type = hashAlg
    signer = PKCS1_v1_5.new(priv_key)
    if (hash_type == "SHA-512"):
        digest = SHA512.new()
    elif (hash_type == "SHA-384"):
        digest = SHA384.new()
    elif (hash_type == "SHA-256"):
        digest = SHA256.new()
    elif (hash_type == "SHA-1"):
        digest = SHA.new()
    else:
        digest = MD5.new()
    digest.update(message)
    return signer.sign(digest)


def verify(message, signature, pub_key):
    signer = PKCS1_v1_5.new(pub_key)
    if (hash_type == "SHA-512"):
        digest = SHA512.new()
    elif (hash_type == "SHA-384"):
        digest = SHA384.new()
    elif (hash_type == "SHA-256"):
        digest = SHA256.new()
    elif (hash_type == "SHA-1"):
        digest = SHA.new()
    else:
        digest = MD5.new()
    digest.update(message)
    return signer.verify(digest, signature)


def main():
    msg1 = b"Hello Tony, I am Jarvis!"
    msg2 = b"Hello Toni, I am Jarvis!"

    keysize = 2048

    (public, private) = rsa.newkeys(keysize)

    # https://docs.python.org/3/library/base64.html
    # encodes the bytes-like object s
    # returns bytes
    # //@todo: should we encode with private key? isn't it supposed to be public key
    encrypted = b64encode(rsa.encrypt(msg1, private))
    # decodes the Base64 encoded bytes-like object or ASCII string s
    # returns the decoded bytes
    decrypted = rsa.decrypt(b64decode(encrypted), private)
    signature = b64encode(rsa.sign(msg1, private, "SHA-512"))

    verify = rsa.verify(msg1, b64decode(signature), public)

    # print(private.exportKey('PEM'))
    # print(public.exportKey('PEM'))
    print("Encrypted: " + encrypted.decode('ascii'))
    print("Decrypted: '%s'" % (decrypted))
    print("Signature: " + signature.decode('ascii'))
    print("Verify: %s" % verify)
    rsa.verify(msg2, b64decode(signature), public)  # msg2 doesn't get verified since it's signature is different.


pub, pri = newkeys(1024)
new_pub = pub.exportKey("DER")
new_new_pub = importKey(new_pub)
print(pub)

if __name__ == "__main__":
    main()
