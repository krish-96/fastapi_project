# refresh tokens stored in DB/Redis, not JWT
# each use rotates to a new token (old one revoked)
async def rotate_refresh_token(old_token: str, db: AsyncSession) -> str:
    token_row = await db.get(RefreshToken, old_token)
    if not token_row or token_row.revoked:
        raise HTTPException(401, "Invalid refresh token")
    token_row.revoked = True
    new_token = secrets.token_urlsafe(32)
    db.add(RefreshToken(token=new_token, user_id=token_row.user_id))
    await db.commit()
    return new_token