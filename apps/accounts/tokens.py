from django.core import signing
from django.conf import settings

TOKEN_SALT = "freelancerhub.email.verify"

def make_verify_token(user_id: int) -> str:
    # signed token includes user id
    return signing.dumps({"uid": user_id}, salt=TOKEN_SALT)

def read_verify_token(token: str) -> int:
    data = signing.loads(token, salt=TOKEN_SALT, max_age=60 * 60 * 24 * 3)  # 3 days
    return int(data["uid"])
