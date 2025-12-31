#/backend/app/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer , HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import crud, models
from .config import settings
from .schemas import TokenData
from typing import Dict
from .database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)


token_blacklist: Dict[str, datetime] = {}

def add_to_blacklist(token: str, expires: datetime):
    token_blacklist[token] = expires

def is_blacklisted(token: str) -> bool:
    expiry = token_blacklist.get(token)
    return expiry and expiry > datetime.utcnow()

# Add to existing auth.py
def create_24h_token(data: dict):
    """Specifically for 24-hour sessions"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def detect_user_role(user: models.User) -> str:
    """Enhanced role detection from ID pattern"""
    if user.role == "admin":
        return "admin"
    # Check ID pattern: YYYYRRDDDXXX
    role_code = user.id[4:6]
    return {
        "01": "admin",
        "02": "teacher",
        "03": "student"
    }.get(role_code, "student")  # Default to student if unknown
def create_password_reset_token(email: str):
    """Token specifically for password reset (1 hour expiry)"""
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {"sub": email, "exp": expire, "type": "reset"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})  # Add token type
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)





async def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    """Now uses verify_token_type dependency"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_email(db= db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user
