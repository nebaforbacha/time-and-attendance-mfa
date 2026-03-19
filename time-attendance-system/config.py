import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production-2024'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///attendance_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application settings
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_TIMEOUT = timedelta(minutes=15)
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # MFA settings
    MFA_ISSUER_NAME = 'Time & Attendance System'
    
    # Email configuration (using Gmail as example)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'cheohsuhneba@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'izqiguxynnwuitew' 
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'Time & Attendance System <noreply@attendance.com>'
    
    # Password reset token expiry
    PASSWORD_RESET_EXPIRY = timedelta(hours=1)