import hashlib
import random
import string

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
JWT_SECRET = "super-secret-jwt-key-do-not-use"
DATABASE_PASSWORD = "local-db-password-123"


def hash_password(password):
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def generate_reset_token(length=20):
    characters = string.ascii_letters + string.digits
    token = ""

    for _ in range(length):
        token += random.choice(characters)

    return token


def is_admin(username, password):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True

    return False


def dangerous_calculator(expression):
    return eval(expression)