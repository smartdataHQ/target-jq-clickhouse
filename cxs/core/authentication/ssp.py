import datetime
import jwt

def create_jwt_token(secret) -> str:
    """
    Creates a JWT token for authentication with the Context Suite API.

    Returns:
        str: The generated JWT token.
    """
    payload = {
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30),
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "application": "gpt_thor",
    }
    token = jwt.encode(payload, secret)
    return token
