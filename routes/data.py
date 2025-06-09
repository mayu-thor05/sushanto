# from flask import Blueprint, request, jsonify, current_app
# from pymongo import MongoClient
# from bson import ObjectId
# from utils.auth import get_user_from_token
# from jsonschema import validate, ValidationError
# from datetime import datetime

# # Updated schema with new fields
# data_schema = {
#     "type": "object",
#     "properties": {
#         "documentName": {"type": "string"},
#         "generationType": {"type": "string", "enum": ["single", "bulk"]},
#         "market_name": {"type": "string"},
#         "Segment1": {"type": "string"},
#         "Segment1Sub-segment1": {"type": "string"},
#         "Segment1Sub-segment2": {"type": "string"},
#         "Segment1Sub-segment3": {"type": "string"},
#         "Segment1Sub-segment4": {"type": "string"},
#         "Segment1Sub-segment5": {"type": "string"},
#         "Segment1Sub-segment6": {"type": "string"},
#         "Segment1Sub-segment7": {"type": "string"},
#         "Segment1Sub-segment8": {"type": "string"},
#         "Segment1Sub-segment9": {"type": "string"},
#         "Segment1Sub-segment10": {"type": "string"},
#         "Segment2": {"type": "string"},
#         "Segment2Sub-segment1": {"type": "string"},
#         "Segment2Sub-segment2": {"type": "string"},
#         "Segment2Sub-segment3": {"type": "string"},
#         "Segment2Sub-segment4": {"type": "string"},
#         "Segment2Sub-segment5": {"type": "string"},
#         "Segment2Sub-segment6": {"type": "string"},
#         "Segment2Sub-segment7": {"type": "string"},
#         "Segment2Sub-segment8": {"type": "string"},
#         "Segment2Sub-segment9": {"type": "string"},
#         "Segment2Sub-segment10": {"type": "string"},
#         "Segment3": {"type": "string"},
#         "Segment3Sub-segment1": {"type": "string"},
#         "Segment3Sub-segment2": {"type": "string"},
#         "Segment3Sub-segment3": {"type": "string"},
#         "Segment3Sub-segment4": {"type": "string"},
#         "Segment3Sub-segment5": {"type": "string"},
#         "Segment3Sub-segment6": {"type": "string"},
#         "Segment3Sub-segment7": {"type": "string"},
#         "Segment3Sub-segment8": {"type": "string"},
#         "Segment3Sub-segment9": {"type": "string"},
#         "Segment3Sub-segment10": {"type": "string"},
#         "Segment4": {"type": "string"},
#         "Segment4Sub-segment1": {"type": "string"},
#         "Segment4Sub-segment2": {"type": "string"},
#         "Segment4Sub-segment3": {"type": "string"},
#         "Segment4Sub-segment4": {"type": "string"},
#         "Segment4Sub-segment5": {"type": "string"},
#         "Segment4Sub-segment6": {"type": "string"},
#         "Segment4Sub-segment7": {"type": "string"},
#         "Segment4Sub-segment8": {"type": "string"},
#         "Segment4Sub-segment9": {"type": "string"},
#         "Segment4Sub-segment10": {"type": "string"},
#         "Segment5": {"type": "string"},
#         "Segment5Sub-segment1": {"type": "string"},
#         "Segment5Sub-segment2": {"type": "string"},
#         "Segment5Sub-segment3": {"type": "string"},
#         "Segment5Sub-segment4": {"type": "string"},
#         "Segment5Sub-segment5": {"type": "string"},
#         "Segment5Sub-segment6": {"type": "string"},
#         "Segment5Sub-segment7": {"type": "string"},
#         "Segment5Sub-segment8": {"type": "string"},
#         "Segment5Sub-segment9": {"type": "string"},
#         "Segment5Sub-segment10": {"type": "string"},
#         "Segment6": {"type": "string"},
#         "Segment6Sub-segment1": {"type": "string"},
#         "Segment6Sub-segment2": {"type": "string"},
#         "Segment6Sub-segment3": {"type": "string"},
#         "Segment6Sub-segment4": {"type": "string"},
#         "Segment6Sub-segment5": {"type": "string"},
#         "Segment6Sub-segment6": {"type": "string"},
#         "Segment6Sub-segment7": {"type": "string"},
#         "Segment6Sub-segment8": {"type": "string"},
#         "Segment6Sub-segment9": {"type": "string"},
#         "Segment6Sub-segment10": {"type": "string"},
#         # ... (rest of your existing segments)
#         "Company1": {"type": "string"},
#         "Company2": {"type": "string"},
#         "Company3": {"type": "string"},
#         "Company4": {"type": "string"},
#         "Company5": {"type": "string"},
#         "Company6": {"type": "string"},
#         "Company7": {"type": "string"},
#         "Company8": {"type": "string"},
#         "Company9": {"type": "string"},
#         "Company10": {"type": "string"},
#     },
#     "required": ["documentName", "generationType", "market_name"]
# }

# bp = Blueprint('data', __name__, url_prefix='/data')

# def get_db():
#     client = MongoClient(current_app.config["MONGODB_URI"])
#     db = client.get_default_database()
#     return db

# @bp.route('/upload', methods=['POST'])
# def upload_data():
#     db = get_db()
#     documents_collection = db.documents
#     token = request.headers.get('Authorization')
#     if not token:
#         return jsonify({"message": "Token is required"}), 401
#     user = get_user_from_token(token)
#     if not user:
#         return jsonify({"message": "Invalid token"}), 401

#     data = request.get_json()

#     try:
#         validate(instance=data, schema=data_schema)
#     except ValidationError as e:
#         current_app.logger.warning(f'Data validation failed for user {user["username"]}: {e.message}')
#         return jsonify({"message": f"Invalid data: {e.message}"}), 400

#     if not data:
#         current_app.logger.warning(f"Upload attempt failed, no data provided, user {user['username']}")
#         return jsonify({"message": "No data provided"}), 400

#     # Add metadata
#     data['user_id'] = str(user['_id'])
#     data['createdBy'] = user['username']
#     data['createdAt'] = datetime.utcnow().isoformat()

#     documents_collection.insert_one(data)
#     current_app.logger.info(f"Data uploaded successfully by user {user['username']}")
#     return jsonify({'message': 'Data uploaded successfully'}), 201

# @bp.route('/records', methods=['GET'])
# def get_records():
#     db = get_db()
#     documents_collection = db.documents
#     token = request.headers.get('Authorization')
#     if not token:
#         return jsonify({"message": "Token is required"}), 401
#     user = get_user_from_token(token)
#     if not user:
#         return jsonify({"message": "Invalid token"}), 401
    
#     user_id = str(user['_id'])
#     if user['role'] == 'admin':
#         records = list(documents_collection.find({}))
#     else:
#         records = list(documents_collection.find({'user_id': user_id}))
    
#     for record in records:
#         record['_id'] = str(record['_id'])
    
#     current_app.logger.info(f"Records retrieved by user {user['username']}")
#     return jsonify(records), 200

# @bp.route('/records/<record_id>', methods=['DELETE'])
# def delete_record(record_id):
#     db = get_db()
#     documents_collection = db.documents
#     token = request.headers.get('Authorization')
#     if not token:
#         return jsonify({"message": "Token is required"}), 401
#     user = get_user_from_token(token)
#     if not user:
#         return jsonify({"message": "Invalid token"}), 401
#     if user['role'] != 'admin':
#         current_app.logger.warning(f"User {user['username']} attempted to delete record without admin privileges")
#         return jsonify({"message": "Unauthorized"}), 403
    
#     if not ObjectId.is_valid(record_id):
#         current_app.logger.warning(f"Invalid record ID provided {record_id}")
#         return jsonify({'message': 'Invalid record ID'}), 400

#     result = documents_collection.delete_one({'_id': ObjectId(record_id)})
#     if result.deleted_count > 0:
#         current_app.logger.info(f"Record deleted by user {user['username']}")
#         return jsonify({'message': 'Record deleted successfully'}), 200
#     else:
#         return jsonify({'message': 'Record not found'}), 404