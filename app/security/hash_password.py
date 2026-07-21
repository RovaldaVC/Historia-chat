# -- Imports -- #
from passlib.context import CryptContext

# Here we set up the logic of argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# This is the Hashing logic for passwords 
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# This way we verify the passwords that has been hashed.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -- We hash passwords for security matters, if attackers get the passwords they won't be able to see the raw passwords so they can't use your password to get inside your account in other sites (if you used the same password) 