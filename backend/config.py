import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # External API URLs
    CRM_API_URL = os.environ.get('CRM_API_URL', 'http://localhost:3001')
    CREDIT_BUREAU_API_URL = os.environ.get('CREDIT_BUREAU_API_URL', 'http://localhost:3002')
    OFFER_MART_API_URL = os.environ.get('OFFER_MART_API_URL', 'http://localhost:3003')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}