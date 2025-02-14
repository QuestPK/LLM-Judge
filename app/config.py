import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    DEBUG = True
    MONGO_URI = os.getenv("MONGO_URI")  # Load from .env