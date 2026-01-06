"""
Pytest configuration and fixtures for testing user management
"""
import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables before importing app to avoid sys.exit()
os.environ.setdefault('WEB_SECRET_KEY', 'test-secret-key-for-testing-only-32-chars')
os.environ.setdefault('ENCRYPTION_KEY', 'test-encryption-key-32-chars-long!!')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('BOT_TOKEN', '123456789:test-token')
os.environ.setdefault('ADMIN_USER_ID', '123456789')

from database.db_manager import DatabaseManager
from database.models import Base, User, Account, Transaction, Lock
from web.app import app
from web.auth import WebUser


@pytest.fixture(scope='function')
def test_db():
    """Create a test database in memory"""
    # Use in-memory SQLite for testing
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    # Create a test DatabaseManager instance
    test_db_manager = DatabaseManager.__new__(DatabaseManager)
    test_db_manager.engine = engine
    test_db_manager.SessionLocal = SessionLocal
    
    yield test_db_manager
    
    # Cleanup
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='function')
def test_client(test_db):
    """Create a test Flask client"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Monkey patch db_manager in app module
    import web.app
    original_app_db = web.app.db_manager
    web.app.db_manager = test_db
    
    # Also patch auth module
    from web import auth
    original_auth_db = getattr(auth.load_user, 'db_manager', None)
    auth.load_user.db_manager = test_db
    
    with app.test_client() as client:
        yield client
    
    # Restore original db_manager
    web.app.db_manager = original_app_db
    if original_auth_db:
        auth.load_user.db_manager = original_auth_db


@pytest.fixture
def admin_user(test_db):
    """Create an admin user for testing"""
    session = test_db.get_session()
    try:
        user = User(
            user_id='admin_test',
            username='admin_test',
            is_admin=True,
            agreement_accepted=True,
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        return user.user_id
    finally:
        session.close()


@pytest.fixture
def regular_user(test_db):
    """Create a regular user for testing"""
    session = test_db.get_session()
    try:
        user = User(
            user_id='user_test_1',
            username='user_test_1',
            is_admin=False,
            agreement_accepted=True,
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        return user.user_id
    finally:
        session.close()


@pytest.fixture
def multiple_users(test_db):
    """Create multiple users for testing pagination and filtering"""
    session = test_db.get_session()
    try:
        users = []
        for i in range(15):
            user = User(
                user_id=f'user_test_{i}',
                username=f'user_test_{i}',
                is_admin=False,
                agreement_accepted=True,
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            session.add(user)
            users.append(user.user_id)
            
            # Add account for some users
            if i % 2 == 0:
                from utils.encryption import hash_password
                account = Account(
                    account_number=f'123456789012345{i:02d}',
                    user_id=user.user_id,
                    password_hash=hash_password('12345678'),
                    balance=Decimal('1000.00') + Decimal(str(i * 100)),
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                session.add(account)
        
        # Add one locked user
        locked_user = User(
            user_id='locked_user',
            username='locked_user',
            is_admin=False,
            agreement_accepted=True,
            created_at=datetime.utcnow()
        )
        session.add(locked_user)
        users.append(locked_user.user_id)
        
        # Create lock for locked user
        lock = Lock(
            user_id=locked_user.user_id,
            reason='Test lock',
            locked_until=datetime.utcnow() + timedelta(days=1)
        )
        session.add(lock)
        
        session.commit()
        return users
    finally:
        session.close()


@pytest.fixture
def logged_in_admin(test_client, admin_user, test_db):
    """Login as admin user"""
    # Manually set session data to simulate login
    with test_client.session_transaction() as sess:
        sess['_user_id'] = admin_user
        sess['_fresh'] = True
    
    return test_client
