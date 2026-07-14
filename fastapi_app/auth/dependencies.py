from typing import Annotated


from fastapi.security import OAuth2PasswordBearer



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user    = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    return user