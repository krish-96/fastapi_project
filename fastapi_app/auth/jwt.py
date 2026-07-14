import jwt  # PyJWT

def create_access_token(data: dict) -> str:
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=30)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")