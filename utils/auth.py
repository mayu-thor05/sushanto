from flask import current_app
from datetime import datetime, timedelta
from bcrypt import checkpw
from pymongo import MongoClient
from bson.objectid import ObjectId
from jose import jwt as jose_jwt

def create_token(payload):
    """Generates a JWT token with a 3-hour expiration time."""
    payload['exp'] = datetime.utcnow() + timedelta(hours=3)
    secret_key = current_app.config['SECRET_KEY']
    return jose_jwt.encode(payload, secret_key, algorithm='HS256')

def authenticate_user(password, hashed_password):
    """Authenticates a user's password against a stored hashed password."""
    return checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_user_from_token(token):
    """Retrieves user data from a JWT token."""
    try:
        # Strip 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
            
        secret_key = current_app.config['SECRET_KEY']
        payload = jose_jwt.decode(token, secret_key, algorithms=['HS256'])
        user_id = payload.get("user_id")
        
        # Get database connection from current app
        db = current_app.db
        users_collection = db.users
        
        # Log the user ID we're looking up
        current_app.logger.info(f"Looking up user with ID: {user_id}")
        
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if user:
            current_app.logger.info(f"Found user: {user.get('username', 'unknown')}")
            return user
        else:
            current_app.logger.warning(f"No user found with ID: {user_id}")
            
    except jose_jwt.ExpiredSignatureError:
        current_app.logger.error("Token has expired")
        return None
    except jose_jwt.JWTError as e:
        current_app.logger.error(f"JWT validation error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error in get_user_from_token: {str(e)}")
        return None
        
    return None