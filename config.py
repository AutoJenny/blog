import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-llm-actions-branch'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://localhost/blog'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True 