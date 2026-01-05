"""
Authentication and authorization for web interface
"""
from flask_login import UserMixin, LoginManager
from database.db_manager import DatabaseManager
import config

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'لطفا برای دسترسی به این صفحه وارد شوید.'
login_manager.login_message_category = 'info'


class WebUser(UserMixin):
    """
    Web user class for Flask-Login
    Uses Telegram user_id as the id
    """
    def __init__(self, user_id: str, db_manager: DatabaseManager):
        self.id = user_id
        self.db_manager = db_manager
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.db_manager.is_admin(self.id)
    
    @staticmethod
    def get(user_id: str, db_manager: DatabaseManager):
        """Get user by user_id"""
        if db_manager.is_admin(user_id):
            return WebUser(user_id, db_manager)
        return None


@login_manager.user_loader
def load_user(user_id: str):
    """Load user for Flask-Login"""
    # This will be set up in app.py
    if not hasattr(load_user, 'db_manager'):
        return None
    return WebUser.get(user_id, load_user.db_manager)
