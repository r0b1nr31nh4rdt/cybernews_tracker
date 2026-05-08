import bcrypt
from database import get_user

def verify_user(username, password):
    user = get_user(username)
    if not user:
        return None
    stored_hash = user[2]  # password spalte
    if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return {"username": user[1], "role": user[3]}
    return None