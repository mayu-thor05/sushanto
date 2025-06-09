import datetime

class User:
    def __init__(self, username, password, role='user', status='active'):
        self.username = username
        self.password = password
        self.role = role
        self.status = status
        self.created_at = datetime.utcnow().isoformat()
        
    def to_dict(self):
        """Convert User object to dictionary for MongoDB storage"""
        return {
            'username': self.username,
            'password': self.password,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        """Create User object from dictionary"""
        user = User(
            username=data['username'],
            password=data['password'],
            role=data.get('role', 'user'),
            status=data.get('status', 'active')
        )
        user.created_at = data.get('created_at', datetime.utcnow().isoformat())
        return user