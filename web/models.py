from flask_login import UserMixin


class AdminUser(UserMixin):
    """Admin user model for Flask-Login"""
    
    def __init__(self, id, username):
        self.id = id
        self.username = username
    
    def get_id(self):
        return str(self.id)
