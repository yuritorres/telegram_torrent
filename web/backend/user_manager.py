#!/usr/bin/env python3
"""
User Management System
Handles user CRUD operations with JSON file storage
"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManager:
    def __init__(self, storage_path: str = "appstore_data/users.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage()
        self._ensure_default_admin()
    
    def _ensure_storage(self):
        """Ensure storage file exists"""
        if not self.storage_path.exists():
            self._save_users([])
    
    def _ensure_default_admin(self):
        """Ensure default admin user exists"""
        users = self._load_users()
        admin_exists = any(u['username'] == 'admin' for u in users)
        
        if not admin_exists:
            default_admin = {
                'id': str(uuid.uuid4()),
                'username': 'admin',
                'email': 'admin@telegram-torrent.local',
                'password_hash': pwd_context.hash('admin'),
                'role': 'admin',
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            users.append(default_admin)
            self._save_users(users)
            logger.info("Default admin user created")
    
    def _load_users(self) -> List[Dict]:
        """Load users from storage"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_users(self, users: List[Dict]):
        """Save users to storage"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
            raise
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (without password hashes)"""
        users = self._load_users()
        return [{k: v for k, v in user.items() if k != 'password_hash'} for user in users]
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        users = self._load_users()
        for user in users:
            if user['id'] == user_id:
                return {k: v for k, v in user.items() if k != 'password_hash'}
        return None
    
    def get_user_by_username(self, username: str, include_password: bool = False) -> Optional[Dict]:
        """Get user by username"""
        users = self._load_users()
        for user in users:
            if user['username'] == username:
                if include_password:
                    return user
                return {k: v for k, v in user.items() if k != 'password_hash'}
        return None
    
    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> Dict:
        """Create a new user"""
        users = self._load_users()
        
        # Check if username already exists
        if any(u['username'] == username for u in users):
            raise ValueError(f"Username '{username}' already exists")
        
        # Check if email already exists
        if any(u['email'] == email for u in users):
            raise ValueError(f"Email '{email}' already exists")
        
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'email': email,
            'password_hash': pwd_context.hash(password),
            'role': role,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        users.append(new_user)
        self._save_users(users)
        
        logger.info(f"User created: {username}")
        return {k: v for k, v in new_user.items() if k != 'password_hash'}
    
    def update_user(self, user_id: str, **kwargs) -> Optional[Dict]:
        """Update user information"""
        users = self._load_users()
        
        for i, user in enumerate(users):
            if user['id'] == user_id:
                # Update allowed fields
                allowed_fields = ['email', 'role', 'is_active']
                for field in allowed_fields:
                    if field in kwargs:
                        user[field] = kwargs[field]
                
                # Update password if provided
                if 'password' in kwargs:
                    user['password_hash'] = pwd_context.hash(kwargs['password'])
                
                user['updated_at'] = datetime.now().isoformat()
                users[i] = user
                self._save_users(users)
                
                logger.info(f"User updated: {user['username']}")
                return {k: v for k, v in user.items() if k != 'password_hash'}
        
        return None
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        users = self._load_users()
        
        # Prevent deleting the last admin
        user_to_delete = next((u for u in users if u['id'] == user_id), None)
        if user_to_delete and user_to_delete['role'] == 'admin':
            admin_count = sum(1 for u in users if u['role'] == 'admin')
            if admin_count <= 1:
                raise ValueError("Cannot delete the last admin user")
        
        initial_count = len(users)
        users = [u for u in users if u['id'] != user_id]
        
        if len(users) < initial_count:
            self._save_users(users)
            logger.info(f"User deleted: {user_id}")
            return True
        
        return False
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        user = self.get_user_by_username(username, include_password=True)
        if not user:
            return False
        
        if not user.get('is_active', False):
            return False
        
        try:
            return pwd_context.verify(password, user['password_hash'])
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        users = self._load_users()
        
        for i, user in enumerate(users):
            if user['id'] == user_id:
                # Verify old password
                if not pwd_context.verify(old_password, user['password_hash']):
                    raise ValueError("Current password is incorrect")
                
                # Update password
                user['password_hash'] = pwd_context.hash(new_password)
                user['updated_at'] = datetime.now().isoformat()
                users[i] = user
                self._save_users(users)
                
                logger.info(f"Password changed for user: {user['username']}")
                return True
        
        return False
