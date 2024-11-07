import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key")
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/medicine_db")

config = Config()
