from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import time
import os
from datetime import datetime, timezone
from pymongo import MongoClient
import importlib

# First define the logger setup
def setup_logger():
    logger = logging.getLogger('app')
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Add file handler
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # Add stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(stream_handler)
    
    return logger

# Setup MongoDB function
def setup_mongodb(app):
    """Initialize MongoDB connection and setup collections"""
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            if "MONGODB_URI" not in app.config:
                raise ValueError("MONGODB_URI not found in configuration")
                
            client = MongoClient(app.config["MONGODB_URI"])
            # Test the connection
            client.admin.command('ping')
            
            # Explicitly specify database name
            db = client['sushanto']
            
            # Create collections if they don't exist
            if 'users' not in db.list_collection_names():
                db.create_collection('users')
            if 'documents' not in db.list_collection_names():
                db.create_collection('documents')
            
            # Create indexes
            db.users.create_index('username', unique=True)
            db.users.create_index([('role', 1), ('status', 1)])
            db.documents.create_index('user_id')
            db.documents.create_index('createdAt')
            db.documents.create_index([("user_id", 1)])
            db.documents.create_index([("bulk_id", 1)])
            db.documents.create_index([("created_at", -1)])
            
            # Update existing users with new fields
            db.users.update_many(
                {'status': {'$exists': False}},
                {'$set': {'status': 'active'}}
            )
            db.users.update_many(
                {'created_at': {'$exists': False}},
                {'$set': {'created_at': datetime.now(timezone.utc).isoformat()}}
            )
            
            # Add validation rules
            db.command({
                'collMod': 'users',
                'validator': {
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['username', 'password', 'role', 'status'],
                        'properties': {
                            'username': {'bsonType': 'string'},
                            'password': {'bsonType': 'string'},
                            'role': {'enum': ['user', 'admin']},
                            'status': {'enum': ['active', 'restricted']},
                            'created_at': {'bsonType': 'string'}
                        }
                    }
                }
            })
            
            app.logger.info("MongoDB setup completed successfully!")
            return db
            
        except Exception as e:
            retry_count += 1
            app.logger.error(f"MongoDB connection attempt {retry_count} failed: {str(e)}")
            if retry_count >= max_retries:
                app.logger.critical("Failed to connect to MongoDB after maximum retries")
                raise
            time.sleep(2 ** retry_count)  # Exponential backoff

# Create and configure the app
app = Flask(__name__)

# Import config after app is created
from config import Config
app.config.from_object(Config)

# Setup logger before anything else
logger = setup_logger()
app.logger = logger

# Replace your current CORS configuration in app.py with this comprehensive solution

# Define allowed origins - include all your frontend URLs
allowed_origins = [
    'https://sample-generator.vercel.app', 
    'http://localhost:3000', 
    'https://xplorasoft.com',
    'https://xplorasoft.com/word/generate'
]

app.config['ALLOWED_ORIGINS'] = allowed_origins

# Before request handler - keep this where it is
@app.before_request
def before_request():
    request.start_time = time.time()

# Remove the existing CORS setup using flask_cors extension
# DO NOT use: CORS(app, resources={r"/*": {"origins": allowed_origins, "supports_credentials": True}})

# Instead, implement proper CORS handling manually to ensure consistent behavior
@app.after_request
def add_cors_headers(response):
    # Add timing logging if request.start_time exists
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        app.logger.info(f"{request.method} {request.path} {response.status_code} - {duration:.4f}s")
    
    # Get the origin from the request
    origin = request.headers.get('Origin')
    app.logger.info(f"Request origin: {origin}")
    
    # Only add CORS headers if the origin is allowed
    if origin in allowed_origins:
        app.logger.info(f"Adding CORS headers for origin: {origin}")
        
        # IMPORTANT: Set headers with exact origin for all responses
        response.headers.set('Access-Control-Allow-Origin', origin)
        response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        
        # IMPORTANT: For security, don't use credentials unless absolutely needed
        # If you're not using cookies for authentication, set this to false
        response.headers.set('Access-Control-Allow-Credentials', 'false')
        
        # Allow caching of preflight responses
        response.headers.set('Access-Control-Max-Age', '3600')
    else:
        if origin:  # Only log if an origin was provided
            app.logger.warning(f"Origin not in allowed list: {origin}")
    
    return response

# Properly handle all OPTIONS preflight requests
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    app.logger.info(f"Handling OPTIONS request for path: {path}")
    
    # Create a proper OPTIONS response
    response = app.make_default_options_response()
    
    # Get the origin from the request
    origin = request.headers.get('Origin')
    app.logger.info(f"OPTIONS request origin: {origin}")
    
    # Only add CORS headers if the origin is allowed
    if origin in allowed_origins:
        app.logger.info(f"Adding CORS headers for OPTIONS request from: {origin}")
        
        # Add CORS headers to the response
        response.headers.set('Access-Control-Allow-Origin', origin)
        response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        response.headers.set('Access-Control-Allow-Credentials', 'false')
        response.headers.set('Access-Control-Max-Age', '3600')
    else:
        if origin:  # Only log if an origin was provided
            app.logger.warning(f"OPTIONS request from non-allowed origin: {origin}")
    
    return response

# Initialize MongoDB
with app.app_context():
    try:
        db = setup_mongodb(app)
        app.db = db  # Store database connection in app context
    except Exception as e:
        app.logger.error(f"Failed to initialize MongoDB: {str(e)}")
        # Continue running the application even if DB setup fails


# Import and register blueprints
from routes import auth, word
app.register_blueprint(auth.bp)
app.register_blueprint(word.bp)

# Health check and admin routes
@app.route('/health')
def health_check():
    try:
        # Use the client object to access the admin database
        client = MongoClient(app.config["MONGODB_URI"])
        client.admin.command('ping')
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
    
@app.route('/')
def root():
    return jsonify({"status": "ok"}), 200

@app.route('/admin/logs', methods=['GET'])
def get_logs():
    try:
        from utils.auth import get_user_from_token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is required"}), 401
        user = get_user_from_token(token)
        if not user:
            return jsonify({"message": "Invalid token"}), 401
        if user['role'] != 'admin':
            return jsonify({"message": "Unauthorized"}), 403

        # Get the current path of the app
        current_path = os.path.dirname(os.path.abspath(__file__))
        # Get all the files on the logs folder
        logs_path = os.path.join(current_path, 'logs')
        log_files = [f for f in os.listdir(logs_path) if os.path.isfile(os.path.join(logs_path, f)) and f.endswith(".log")]
        logs = []
        for log_file in log_files:
            file_path = os.path.join(logs_path, log_file)
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        try:
                            parts = line.strip().split(' - ', 2)
                            if len(parts) == 3:
                                timestamp = parts[0]
                                level = parts[1]
                                message = parts[2]
                                logs.append({'timestamp': timestamp, 'level': level, 'message': message})
                        except ValueError:
                            app.logger.warning(f"Error reading line in log file {log_file}")
                            continue
            except FileNotFoundError:
                app.logger.warning(f"Log file not found {log_file}")
                continue
        return jsonify(logs), 200
    except Exception as e:
        app.logger.error(f"Error accessing logs: {str(e)}")
        return jsonify({"message": f"Error: {str(e)}"}), 500
    
# Add this to your app.py file, just before the if __name__ == '__main__': block

@app.route('/cors-test', methods=['GET', 'OPTIONS'])
def cors_test():
    """
    Simple endpoint to test CORS configuration.
    """
    if request.method == 'OPTIONS':
        app.logger.info("Received OPTIONS request to /cors-test")
        # The options_handler should handle this automatically
        return app.make_default_options_response()
    
    # Log the request details
    app.logger.info("Received GET request to /cors-test")
    app.logger.info(f"Request headers: {dict(request.headers)}")
    
    # Create a simple response
    response_data = {
        "status": "success",
        "message": "CORS is configured correctly!",
        "request_headers": dict(request.headers),
        "allowed_origins": allowed_origins,
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(response_data), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)