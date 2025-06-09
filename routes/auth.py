from flask import Blueprint, request, jsonify, current_app
import secrets
import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from bcrypt import hashpw, gensalt
from models.user import User
from utils.auth import authenticate_user, create_token, get_user_from_token

bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_db():
    return current_app.db

# Add new GET users endpoint
@bp.route('/users', methods=['GET'])
def get_users():
    db = get_db()
    users_collection = db.users
    token = request.headers.get('Authorization')
    
    if not token:
        current_app.logger.warning('Get users attempt failed. No token provided')
        return jsonify({"message": "Token is required"}), 401
    
    # Handle Bearer token
    if token.startswith('Bearer '):
        token = token.split(' ')[1]
    
    user = get_user_from_token(token)
    if not user or user['role'] != 'admin':
        current_app.logger.warning(f'Get users attempt failed. Unauthorized access')
        return jsonify({"message": "Unauthorized"}), 403

    try:
        # Exclude password field from results
        users = list(users_collection.find({}, {'password': 0}))
        for user in users:
            user['_id'] = str(user['_id'])
        current_app.logger.info('Users retrieved successfully')
        return jsonify(users), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"message": "Error fetching users"}), 500

@bp.route('/register', methods=['POST'])
def register():
    db = get_db()
    users_collection = db.users
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')
    status = data.get('status', 'active')

    if not username or not password:
        current_app.logger.warning(f'Register attempt failed. Missing required fields')
        return jsonify({'message': 'Username and password are required'}), 400

    if users_collection.find_one({'username': username}):
        current_app.logger.warning(f'Register attempt failed. Username already exists')
        return jsonify({'message': 'Username already exists'}), 409

    hashed_password = hashpw(password.encode('utf-8'), gensalt())
    user = User(
        username=username,
        password=hashed_password.decode('utf-8'),
        role=role,
        status=status
    )
    users_collection.insert_one(user.__dict__)
    current_app.logger.info(f'User registered successfully')
    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/users/<user_id>', methods=['PATCH'])
def update_user_status(user_id):
    db = get_db()
    users_collection = db.users
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({"message": "Token is required"}), 401
    
    # Handle Bearer token
    if token.startswith('Bearer '):
        token = token.split(' ')[1]
    
    admin_user = get_user_from_token(token)
    if not admin_user or admin_user['role'] != 'admin':
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status or new_status not in ['active', 'restricted']:
        return jsonify({"message": "Invalid status value"}), 400

    if not ObjectId.is_valid(user_id):
        return jsonify({'message': 'Invalid user ID'}), 400

    result = users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'status': new_status}}
    )

    if result.modified_count > 0:
        current_app.logger.info(f"User status updated by admin {admin_user['username']}")
        return jsonify({'message': 'User status updated successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@bp.route('/login', methods=['POST'])
def login():
    try:
        db = get_db()
        users_collection = db.users
        data = request.get_json()
        
        if not data:
            current_app.logger.warning('Login attempt failed. No JSON data received')
            return jsonify({'message': 'Request must contain JSON data'}), 400
            
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            current_app.logger.warning('Login attempt failed. Missing credentials')
            return jsonify({'message': 'Username and password are required'}), 400

        current_app.logger.info(f'Attempting login for user: {username}')
        user = users_collection.find_one({'username': username})
        
        if not user:
            current_app.logger.warning(f'Login attempt failed. User not found: {username}')
            return jsonify({'message': 'Invalid username or password'}), 401
            
        if not authenticate_user(password, user['password']):
            current_app.logger.warning(f'Login attempt failed. Invalid password for user: {username}')
            return jsonify({'message': 'Invalid username or password'}), 401

        if user.get('status') == 'restricted':
            current_app.logger.warning(f'Login attempt failed. User account is restricted: {username}')
            return jsonify({'message': 'Account is restricted'}), 403

        token = create_token({'user_id': str(user['_id']), 'role': user['role']})
        current_app.logger.info(f'Login successful for user: {username}')
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'role': user['role'],
            'username': user['username']
        }), 200
    except Exception as e:
        current_app.logger.error(f'Unexpected error during login: {str(e)}')
        return jsonify({'message': 'An error occurred during login', 'error': str(e)}), 500
    
@bp.route('/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password():
    db = get_db()
    users_collection = db.users
    reset_tokens_collection = db.password_reset_tokens
    data = request.get_json()
    username = data.get('username')

    if not username:
        current_app.logger.warning('Forgot password attempt failed. No username provided')
        return jsonify({'message': 'Username is required'}), 400

    user = users_collection.find_one({'username': username})
    if not user:
        # Don't reveal if user exists or not
        current_app.logger.info(f'Forgot password request for non-existent user: {username}')
        return jsonify({'message': 'If this account exists, a reset token has been sent'}), 200

    # For admin users, we'll enforce additional verification
    if user['role'] == 'admin':
        # Generate a secure token
        token = secrets.token_urlsafe(32)
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        # Store token in database
        reset_tokens_collection.insert_one({
            'user_id': user['_id'],
            'token': token,
            'expires': expires
        })

        # In a real system, you'd send this token via email
        # For demonstration, we'll just log it - in production, use proper email service
        current_app.logger.info(f'ADMIN PASSWORD RESET TOKEN for {username}: {token}')
        
        return jsonify({'message': 'If this account exists, a reset token has been sent'}), 200
    else:
        # For non-admin users, return same message but don't actually create a token
        # You could implement a different process for regular users if needed
        return jsonify({'message': 'If this account exists, a reset token has been sent'}), 200

@bp.route('/reset-password', methods=['POST'])
def reset_password():
    db = get_db()
    users_collection = db.users
    reset_tokens_collection = db.password_reset_tokens
    data = request.get_json()
    
    token = data.get('token')
    new_password = data.get('password')
    
    if not token or not new_password:
        current_app.logger.warning('Reset password attempt failed. Missing required fields')
        return jsonify({'message': 'Token and new password are required'}), 400
    
    # Find the token document
    token_doc = reset_tokens_collection.find_one({'token': token})
    
    if not token_doc:
        current_app.logger.warning('Reset password attempt failed. Invalid token')
        return jsonify({'message': 'Invalid or expired token'}), 400
    
    # Check if token is expired
    if token_doc['expires'] < datetime.datetime.utcnow():
        reset_tokens_collection.delete_one({'_id': token_doc['_id']})
        current_app.logger.warning('Reset password attempt failed. Token expired')
        return jsonify({'message': 'Token has expired'}), 400
    
    # Get the user
    user = users_collection.find_one({'_id': token_doc['user_id']})
    if not user:
        current_app.logger.warning('Reset password attempt failed. User not found')
        return jsonify({'message': 'User not found'}), 404
    
    # Only allow admin resets through this flow
    if user['role'] != 'admin':
        current_app.logger.warning(f'Reset password attempt failed. Non-admin user attempted admin reset flow')
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Update the password
    hashed_password = hashpw(new_password.encode('utf-8'), gensalt())
    users_collection.update_one(
        {'_id': user['_id']},
        {'$set': {'password': hashed_password.decode('utf-8')}}
    )
    
    # Delete the used token
    reset_tokens_collection.delete_one({'_id': token_doc['_id']})
    
    current_app.logger.info(f'Password reset successful for admin user: {user["username"]}')
    return jsonify({'message': 'Password reset successful'}), 200

@bp.route('/verify-reset-token', methods=['POST'])
def verify_reset_token():
    db = get_db()
    reset_tokens_collection = db.password_reset_tokens
    data = request.get_json()
    
    token = data.get('token')
    
    if not token:
        return jsonify({'message': 'Token is required'}), 400
    
    # Find the token document
    token_doc = reset_tokens_collection.find_one({'token': token})
    
    if not token_doc:
        return jsonify({'valid': False}), 200
    
    # Check if token is expired
    if token_doc['expires'] < datetime.datetime.utcnow():
        reset_tokens_collection.delete_one({'_id': token_doc['_id']})
        return jsonify({'valid': False}), 200
    
    return jsonify({'valid': True}), 200

# User model remains the same
class User:
    def __init__(self, username, password, role='user', status='active'):
        self.username = username
        self.password = password
        self.role = role
        self.status = status