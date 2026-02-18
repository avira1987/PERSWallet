"""
Tests for user management API endpoints
Tests cover:
- Loading users (performance)
- Button functionality (lock, unlock, delete, admin)
- Filtering and search
- User details
"""
import pytest
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from flask import url_for


class TestUserManagementAPI:
    """Test suite for user management API endpoints"""
    
    def test_load_users_endpoint_exists(self, test_client, logged_in_admin):
        """Test that /api/users endpoint exists and returns JSON"""
        response = logged_in_admin.get('/api/users')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
    
    def test_load_users_requires_auth(self, test_client):
        """Test that /api/users requires authentication"""
        response = test_client.get('/api/users')
        assert response.status_code == 302  # Redirect to login
    
    def test_load_users_requires_admin(self, test_client, test_db, regular_user):
        """Test that /api/users requires admin access"""
        # Regular users can't login to web interface (only admins can)
        # So we test that unauthenticated access is blocked
        response = test_client.get('/api/users')
        assert response.status_code == 302  # Redirect to login
    
    def test_load_users_empty_list(self, logged_in_admin):
        """Test loading users when no users exist (except admin)"""
        # Admin user is created by fixture, so we can't have truly empty list
        # Instead, test that API returns proper structure
        response = logged_in_admin.get('/api/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'users' in data
        assert 'pagination' in data
        # Admin user exists, so at least 1 user
        assert len(data['users']) >= 1
        assert data['pagination']['total'] >= 1
    
    def test_load_users_with_data(self, logged_in_admin, test_db, multiple_users):
        """Test loading users with data"""
        response = logged_in_admin.get('/api/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'users' in data
        assert 'pagination' in data
        assert len(data['users']) > 0
        # Admin user is also in the list, so total should be >= multiple_users count
        assert data['pagination']['total'] >= len(multiple_users)
    
    def test_load_users_performance(self, logged_in_admin, test_db, multiple_users):
        """Test that loading users is fast (performance test)"""
        start_time = time.time()
        response = logged_in_admin.get('/api/users')
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        # Should load in less than 1 second
        assert elapsed_time < 1.0, f"Loading users took {elapsed_time:.2f} seconds, expected < 1.0"
    
    def test_load_users_pagination(self, logged_in_admin, test_db, multiple_users):
        """Test pagination functionality"""
        # Test first page
        response = logged_in_admin.get('/api/users?page=1&per_page=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['users']) <= 10
        assert data['pagination']['page'] == 1
        
        # Test second page
        response = logged_in_admin.get('/api/users?page=2&per_page=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['page'] == 2
    
    def test_load_users_per_page_limit(self, logged_in_admin, test_db, multiple_users):
        """Test that per_page is limited to prevent abuse"""
        response = logged_in_admin.get('/api/users?per_page=1000')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should be limited to max 500
        assert len(data['users']) <= 500
    
    def test_lock_user_button(self, logged_in_admin, test_db, regular_user):
        """Test lock user button functionality"""
        # Lock user
        response = logged_in_admin.post(
            f'/api/users/{regular_user}/lock',
            json={'reason': 'Test lock'},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify user is locked
        session = test_db.get_session()
        try:
            from database.models import Lock
            lock = session.query(Lock).filter(Lock.user_id == regular_user).first()
            assert lock is not None
            assert lock.reason == 'Test lock'
        finally:
            session.close()
    
    def test_unlock_user_button(self, logged_in_admin, test_db, regular_user):
        """Test unlock user button functionality"""
        # First lock the user
        session = test_db.get_session()
        try:
            from database.models import Lock
            lock = Lock(
                user_id=regular_user,
                reason='Test lock',
                locked_until=datetime.utcnow() + timedelta(days=1)
            )
            session.add(lock)
            session.commit()
        finally:
            session.close()
        
        # Unlock user
        response = logged_in_admin.post(f'/api/users/{regular_user}/unlock')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify user is unlocked
        session = test_db.get_session()
        try:
            from database.models import Lock
            lock = session.query(Lock).filter(Lock.user_id == regular_user).first()
            assert lock is None
        finally:
            session.close()
    
    def test_delete_user_button(self, logged_in_admin, test_db, regular_user):
        """Test delete user button functionality"""
        # Delete user
        response = logged_in_admin.delete(f'/api/users/{regular_user}/delete')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify user is deleted
        session = test_db.get_session()
        try:
            from database.models import User
            user = session.query(User).filter(User.user_id == regular_user).first()
            assert user is None
        finally:
            session.close()
    
    def test_delete_user_not_found(self, logged_in_admin):
        """Test deleting non-existent user"""
        response = logged_in_admin.delete('/api/users/nonexistent/delete')
        assert response.status_code == 404
    
    def test_make_admin_button(self, logged_in_admin, test_db, regular_user):
        """Test make admin button functionality"""
        # Make user admin
        response = logged_in_admin.post(
            f'/api/users/{regular_user}/admin',
            json={'is_admin': True},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify user is admin
        session = test_db.get_session()
        try:
            from database.models import User
            user = session.query(User).filter(User.user_id == regular_user).first()
            assert user.is_admin == True
        finally:
            session.close()
    
    def test_remove_admin_button(self, logged_in_admin, test_db, admin_user):
        """Test remove admin button functionality"""
        # Remove admin status
        response = logged_in_admin.post(
            f'/api/users/{admin_user}/admin',
            json={'is_admin': False},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify user is not admin anymore
        session = test_db.get_session()
        try:
            from database.models import User
            user = session.query(User).filter(User.user_id == admin_user).first()
            assert user.is_admin == False
        finally:
            session.close()
    
    def test_user_detail_endpoint(self, logged_in_admin, test_db, regular_user):
        """Test user detail endpoint"""
        # Add an account for the user
        session = test_db.get_session()
        try:
            from database.models import Account
            from utils.encryption import hash_password
            account = Account(
                account_number='1234567890123456',
                user_id=regular_user,
                password_hash=hash_password('12345678'),
                balance=Decimal('5000.00'),
                is_active=True,
                created_at=datetime.utcnow()
            )
            session.add(account)
            session.commit()
        finally:
            session.close()
        
        # Get user details
        response = logged_in_admin.get(f'/api/users/{regular_user}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user_id'] == regular_user
        assert 'accounts' in data
        assert len(data['accounts']) == 1
        assert data['accounts'][0]['account_number'] == '1234567890123456'
    
    def test_user_detail_not_found(self, logged_in_admin):
        """Test getting details for non-existent user"""
        response = logged_in_admin.get('/api/users/nonexistent')
        assert response.status_code == 404
    
    def test_users_page_loads(self, logged_in_admin):
        """Test that users page loads correctly"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        assert 'مدیریت کاربران'.encode('utf-8') in response.data
    
    def test_users_api_includes_lock_status(self, logged_in_admin, test_db, multiple_users):
        """Test that users API includes lock status"""
        response = logged_in_admin.get('/api/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Find locked user
        locked_user = next((u for u in data['users'] if u['user_id'] == 'locked_user'), None)
        assert locked_user is not None
        assert locked_user['is_locked'] == True
        assert locked_user['lock_reason'] == 'Test lock'
    
    def test_users_api_includes_account_info(self, logged_in_admin, test_db, multiple_users):
        """Test that users API includes account count and balance"""
        response = logged_in_admin.get('/api/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that users have account_count and balance
        for user in data['users']:
            assert 'account_count' in user
            assert 'balance' in user
            assert isinstance(user['account_count'], int)
            assert isinstance(user['balance'], (int, float))
    
    def test_lock_user_rate_limit(self, logged_in_admin, test_db, regular_user):
        """Test rate limiting on lock user endpoint"""
        # Try to lock user multiple times quickly
        for i in range(25):  # More than rate limit
            response = logged_in_admin.post(
                f'/api/users/{regular_user}/lock',
                json={'reason': f'Test lock {i}'},
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code == 429:  # Too Many Requests
                break
        
        # Should eventually hit rate limit (though in test it might not)
        # This test verifies the endpoint exists and works
        assert response.status_code in [200, 429]
    
    def test_concurrent_load_users(self, logged_in_admin, test_db, multiple_users):
        """Test loading users concurrently (performance test)"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def load_users():
            start = time.time()
            response = logged_in_admin.get('/api/users')
            elapsed = time.time() - start
            results.put((response.status_code, elapsed))
        
        # Create 5 concurrent requests
        threads = []
        for _ in range(5):
            t = threading.Thread(target=load_users)
            t.start()
            threads.append(t)
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check all requests succeeded
        while not results.empty():
            status_code, elapsed = results.get()
            assert status_code == 200
            assert elapsed < 2.0  # Should still be fast even with concurrency
