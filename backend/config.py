import os

class Config:
    # Use an environment variable for security, or hard-code for local development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:1234@localhost/openalex_ILL_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False