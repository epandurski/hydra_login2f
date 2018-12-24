import os
import re
import random
import string
import base64
import struct
import hashlib
from crypt import crypt

EMAIL_REGEX = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
PASSWORD_SALT_CHARS = string.digits + string.ascii_letters + './'


def is_invalid_email(email):
    if len(email) >= 255:
        return True
    return not EMAIL_REGEX.match(email)


def generate_password_salt(method):
    salt = '$%s$' % method if method else ''
    salt += ''.join(random.choice(PASSWORD_SALT_CHARS) for _ in range(16))
    return salt


def generate_random_secret(num_bytes=15):
    return base64.urlsafe_b64encode(os.urandom(num_bytes)).decode('ascii')


def generate_recovery_code(num_bytes=10):
    return base64.b32encode(os.urandom(num_bytes)).decode('ascii')


def normalize_recovery_code(recovery_code):
    return recovery_code.strip().replace(' ', '').replace('0', 'O').replace('1', 'I').upper()


def split_recovery_code_in_blocks(recovery_code, block_size=4):
    if recovery_code is None:
        return ''
    N = block_size
    block_count = (len(recovery_code) + N - 1) // N
    blocks = [recovery_code[N * i:N * i + 4] for i in range(block_count)]
    return ' '.join(blocks)


def generate_verification_code(num_digits=6):
    assert 1 <= num_digits < 10
    random_number = struct.unpack('<L', os.urandom(4))[0] % (10 ** num_digits)
    return str(random_number).zfill(num_digits)


def calc_crypt_hash(salt, message):
    return crypt(message, salt)


def calc_sha256(computer_code):
    m = hashlib.sha256()
    m.update(computer_code.encode())
    return base64.urlsafe_b64encode(m.digest()).decode('ascii')
