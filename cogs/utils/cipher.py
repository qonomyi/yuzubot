import hashlib
import json

from cryptography.fernet import Fernet

import config
from cogs.utils.types import HoYoUserData

fernet = Fernet(config.encrypt_key)
salt = config.hash_salt


def encrypt_user_data(raw_user_data: HoYoUserData) -> str:
    data_dump = json.dumps(raw_user_data)
    encrypted_data = fernet.encrypt(data_dump.encode()).decode()
    return encrypted_data


def decrypt_user_data(encrypted_data) -> HoYoUserData:
    decrypted_data = fernet.decrypt(encrypted_data.encode()).decode()
    return json.loads(decrypted_data)


def hash_user_id(raw_user_id: int) -> str:
    salted_id = str(raw_user_id) + salt
    hashed_id = hashlib.sha256(salted_id.encode()).hexdigest()
    return hashed_id
