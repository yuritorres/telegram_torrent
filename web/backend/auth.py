#!/usr/bin/env python3
"""
Authentication module for Web API Backend
Handles JWT token generation, validation, and password management
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))

WEB_USERNAME = os.getenv('WEB_USERNAME', 'admin')
WEB_PASSWORD_HASH = os.getenv('WEB_PASSWORD_HASH', '')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Token verification error: {e}")
        return None


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user with username and password"""
    if username != WEB_USERNAME:
        return False
    
    if not WEB_PASSWORD_HASH:
        logger.warning("WEB_PASSWORD_HASH not set - using default password 'admin'")
        default_hash = get_password_hash('admin')
        return verify_password(password, default_hash)
    
    return verify_password(password, WEB_PASSWORD_HASH)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    return {"username": username}


def generate_password_hash(password: str) -> str:
    """Utility function to generate password hash for configuration"""
    return get_password_hash(password)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    token: Optional[str] = None
) -> Dict:
    """
    Dependency to get current authenticated user from token.
    Accepts token from either Authorization header or query parameter.
    Used for streaming endpoints where HTML video element cannot send custom headers.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from Authorization header first
    auth_token = None
    if credentials:
        auth_token = credentials.credentials
    # Fall back to query parameter
    elif token:
        auth_token = token
    
    if not auth_token:
        raise credentials_exception
    
    payload = verify_token(auth_token)
    
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    return {"username": username}
