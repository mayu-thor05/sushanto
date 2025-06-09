import os

class Config:
    # Retrieve secret key from environment variable or use default
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    # Retrieve MongoDB connection URI from environment variable or use default
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb+srv://resolvadb1:mayur512@cluster0.sdq2ljq.mongodb.net/sushanto'
    
     # Environment setting
    ENV = os.environ.get('FLASK_ENV', 'production')
    
    # Debug mode (disable in production)
    DEBUG = ENV == 'development'
    
    # Additional configurations
    CORS_ORIGINS = [
        'https://sample-generator.vercel.app',
        'http://localhost:3000'
    ]