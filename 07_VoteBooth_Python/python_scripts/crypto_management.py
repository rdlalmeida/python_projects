from common import utils
import os
import pathlib
import configparser
import random

from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

import logging
log = logging.getLogger(__name__)
utils.configureLogging()

config_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)


test_message: str = "This is ballot option nr 19820301"

def generate_rsa_key_pair():
    key_size: int = 2048

    private_key: rsa.RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    public_key: rsa.RSAPublicKey = private_key.public_key()

    
    return private_key, public_key


def generate_ec_key_pair():
    private_key_ecdsa: ec.EllipticCurvePrivateKey = ec.generate_private_key(
        curve=ec.SECP256R1(),
        backend=default_backend()
    )

    public_key_ecdsa: ec.EllipticCurvePublicKey = private_key_ecdsa.public_key()

    return private_key_ecdsa, public_key_ecdsa


def encrypt_message(plaintext_message: str, public_key) -> str:
    encrypted_message: str = public_key.encrypt(
        plaintext=bytes(plaintext_message, encoding="UTF-8"),
        padding=padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return encrypted_message


def decrypt_message(ciphertext_message: str, private_key) -> str:
    try:
        decrypted_message: str = private_key.decrypt(
            ciphertext=ciphertext_message,
            padding=padding.OAEP(
                padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            )
        )
        return decrypted_message
    except ValueError:
        raise Exception("Unable to decrypt message!")


def sign_message(message_to_sign: str, private_key: rsa.RSAPrivateKey) -> bytes:
    signature: bytes = private_key.sign(
        data=message_to_sign,
        padding=padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        algorithm=hashes.SHA256()
    )

    return signature


def verify_signature(signature: str, signed_message: str, public_key: rsa.RSAPublicKey) -> bool:
    try:
        public_key.verify(
            signature=signature,
            data=signed_message,
            padding=padding.PSS(
                padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            algorithm=hashes.SHA256()
        )

        print("The message was correctly signed!")
        return True
    except InvalidSignature:
        print("Unable to verify the message signature!")
        return False
    
def savePrivateKeyToFile(filename: str, private_key: rsa.RSAPrivateKey) -> None:
    private_pem_text = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    if (filename[:-4] != ".key"):
        filename = filename + ".key"

    file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("keys", filename)

    with open(file=file_path, mode="wb") as file:
        file.write(private_pem_text)


def savePublicKeyToFile(filename:str, public_key: rsa.RSAPublicKey) -> None:
    public_pem_text = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    if (filename[:-4] != ".key"):
        filename = filename + ".key"

    file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("keys", filename)

    with open(file=file_path, mode="wb") as file:
        file.write(public_pem_text)


def loadPrivateKeyFromFile(filename: str) -> rsa.RSAPrivateKey:
    file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("keys", filename)

    if (not file_path.exists()):
        raise FileNotFoundError(f"ERROR: Unable to read a key from {file_path.__str__()}")
    
    with open(file=file_path, mode="rb") as key_file:
        private_key = serialization.load_pem_private_key(
            data=key_file.read(),
            password=None,
            backend=default_backend()
        )

        return private_key
    

def loadPublicKeyFromFile(filename:str) -> rsa.RSAPublicKey:
    file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("keys", filename)

    if (not file_path.exists()):
        raise FileNotFoundError(f"ERROR: Unable to read a key from {file_path.__str__()}")
    
    with open(file=file_path, mode="rb") as key_file:
        public_key = serialization.load_pem_public_key(
            data=key_file.read(),
            backend=default_backend()
        )

        return public_key
    

def serializeKey(public_key: rsa.RSAPublicKey) -> str:
    public_key_bytes = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

    return public_key_bytes

def deserializeKey(public_key_string: str) -> rsa.RSAPublicKey:
    # public_key_bytes = bytes(public_key_string, encoding="UTF-8")

    public_key = serialization.load_pem_public_key(
        public_key_string,
        backend=default_backend()
    )

    return public_key

def main():
    # rsa_private_k1, rsa_public_k1 = generate_rsa_key_pair()
    # rsa_private_k2, rsa_public_k2 = generate_rsa_key_pair()
    # rsa_private_k3, rsa_public_k3 = generate_rsa_key_pair()

    # serial_public_k1 = serializeKey(public_key=rsa_public_k1)
    # serial_public_k2 = serializeKey(public_key=rsa_public_k2)
    # serial_public_k3 = serializeKey(public_key=rsa_public_k3)

    # log.info(f"Key 1 = {serial_public_k1.hex()}")
    # log.info(f"Key 2 = {serial_public_k2.hex()}")
    # log.info(f"Key 3 = {serial_public_k3.hex()}")

    # serial64_public_k1 = base64.b64encode(serial_public_k1)
    # serial64_public_k2 = base64.b64encode(serial_public_k2)
    # serial64_public_k3 = base64.b64encode(serial_public_k3)

    # log.info(f"Base 64 key 1 = {serial64_public_k1.__str__()}")
    # log.info(f"Base 64 key 2 = {serial64_public_k2.__str__()}")
    # log.info(f"Base 64 key 3 = {serial64_public_k3.__str__()}")

    # savePrivateKeyToFile(filename="rsa_private_1", private_key=rsa_private_k1)
    # savePrivateKeyToFile(filename="rsa_private_2", private_key=rsa_private_k2)
    # savePrivateKeyToFile(filename="rsa_private_3", private_key=rsa_private_k3)

    # savePublicKeyToFile(filename="rsa_public_1", public_key=rsa_public_k1)
    # savePublicKeyToFile(filename="rsa_public_2", public_key=rsa_public_k2)
    # savePublicKeyToFile(filename="rsa_public_3", public_key=rsa_public_k3)
    log.info("OK!")


main()