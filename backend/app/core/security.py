"""
Security utilities including password hashing and JWT token processing.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if a plain text password matches its hashed equivalent using bcrypt directly.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Generates a secure password hash using bcrypt directly with configured rounds.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def create_jwt_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: Optional[dict[str, Any]] = None
) -> str:
    """
    Generates a signed JWT token containing subject, type, iat, exp, and jti claims.
    """
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    claims = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid4())
    }
    
    if additional_claims:
        claims.update(additional_claims)
        
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_jwt_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decodes and validates a JWT token signature and expiration.
    Returns the claims dict if successful, otherwise None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
