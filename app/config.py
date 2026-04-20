import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-prod'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Config
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # DB Config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/creapay'
    
    # Redis & Celery Config
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Custom Constants
    FREE_DEAL_LIMIT = 3
    PRO_PLAN_PRICE = 29900 # paise

class DevConfig(Config):
    DEBUG = True
    # In dev, we can use sqlite if postgres is not available
    if not os.environ.get('DATABASE_URL'):
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProdConfig(Config):
    DEBUG = False
    # Prod should always use postgres, DATABASE_URL must be set

config = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
    'default': DevConfig
}
