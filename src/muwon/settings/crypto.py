from cryptography.fernet import Fernet


def encrypt(plaintext: str, master_key: str) -> str:
    return Fernet(master_key.encode()).encrypt(plaintext.encode()).decode()


def decrypt(token: str, master_key: str) -> str:
    return Fernet(master_key.encode()).decrypt(token.encode()).decode()


def generate_master_key() -> str:
    return Fernet.generate_key().decode()
