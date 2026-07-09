import datetime
from typing import Optional, Union, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    import jwt
except ImportError:
    jwt = None

try:
    import bcrypt
except ImportError:
    bcrypt = None

import hashlib
from backend.app.core.config import settings
from backend.app.core.db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Fallback password hashing using hashlib
def _fallback_hash(password: str) -> str:
    salt = settings.SECRET_KEY[:16].encode('utf-8')
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if bcrypt:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            pass
    # fallback
    return _fallback_hash(plain_password) == hashed_password

def get_password_hash(password: str) -> str:
    if bcrypt:
        try:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        except Exception:
            pass
    return _fallback_hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    
    if jwt:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    else:
        # Simple fallback token if PyJWT is not installed
        import json, base64
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().strip("=")
        payload = base64.urlsafe_b64encode(json.dumps(to_encode, default=str).encode()).decode().strip("=")
        return f"{header}.{payload}.fallback_signature"

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if jwt:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
        else:
            import base64, json
            parts = token.split(".")
            if len(parts) >= 2:
                payload_data = base64.urlsafe_b64decode(parts[1] + "===").decode()
                payload = json.loads(payload_data)
                user_id = payload.get("sub")
            else:
                user_id = None
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    from backend.app.models import User
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise credentials_exception
    return user

async def get_current_admin(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user
