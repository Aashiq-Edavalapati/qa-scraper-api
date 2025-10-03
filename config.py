# /config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    GNEWS_API_KEY = os.environ.get('GNEWS_API_KEY')
    SERPAPI_API_KEY = os.environ.get('SERPAPI_API_KEY')