"""
Tests for user management frontend functionality
Tests cover:
- JavaScript functions
- Button click handlers
- Filter and search functionality
- Modal interactions
"""
import pytest
from bs4 import BeautifulSoup


class TestUserManagementFrontend:
    """Test suite for user management frontend"""
    
    def test_users_page_has_search_input(self, logged_in_admin):
        """Test that users page has search input field"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        search_input = soup.find('input', {'id': 'search-input'})
        assert search_input is not None
        assert search_input.get('placeholder') == 'جستجوی کاربر (User ID)'
    
    def test_users_page_has_filter_dropdown(self, logged_in_admin):
        """Test that users page has filter dropdown"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        filter_select = soup.find('select', {'id': 'filter-lock'})
        assert filter_select is not None
        
        # Check filter options
        options = filter_select.find_all('option')
        option_values = [opt.get('value') for opt in options]
        assert '' in option_values  # All users
        assert 'locked' in option_values  # Locked only
        assert 'unlocked' in option_values  # Unlocked only
    
    def test_users_page_has_refresh_button(self, logged_in_admin):
        """Test that users page has refresh button"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        refresh_btn = soup.find('button', {'id': 'refresh-btn'})
        assert refresh_btn is not None
        assert 'بروزرسانی' in refresh_btn.get_text()
    
    def test_users_page_has_table(self, logged_in_admin):
        """Test that users page has users table"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        table = soup.find('table', {'id': 'users-table'})
        assert table is not None
        
        # Check table headers
        headers = table.find('thead')
        assert headers is not None
        header_texts = [th.get_text().strip() for th in headers.find_all('th')]
        assert 'User ID' in header_texts
        assert 'Username' in header_texts
        assert 'عملیات' in header_texts
    
    def test_users_page_has_modals(self, logged_in_admin):
        """Test that users page has required modals"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # User detail modal
        user_detail_modal = soup.find('div', {'id': 'userDetailModal'})
        assert user_detail_modal is not None
        
        # Balance modal
        balance_modal = soup.find('div', {'id': 'balanceModal'})
        assert balance_modal is not None
        
        # Reset password modal
        password_modal = soup.find('div', {'id': 'resetPasswordModal'})
        assert password_modal is not None
    
    def test_users_page_has_javascript_functions(self, logged_in_admin):
        """Test that users page includes JavaScript functions"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        # Check for JavaScript functions in the page
        assert b'function loadUsers' in response.data
        assert b'function lockUser' in response.data
        assert b'function unlockUser' in response.data
        assert b'function deleteUser' in response.data
        assert b'function makeAdmin' in response.data
        assert b'function removeAdmin' in response.data
        assert b'function showUserDetail' in response.data
    
    def test_users_page_has_csrf_token(self, logged_in_admin):
        """Test that users page includes CSRF token"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        assert csrf_meta is not None
        assert csrf_meta.get('content') is not None
    
    def test_users_table_has_tbody(self, logged_in_admin):
        """Test that users table has tbody element"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        tbody = soup.find('tbody', {'id': 'users-tbody'})
        assert tbody is not None
    
    def test_users_page_loads_bootstrap(self, logged_in_admin):
        """Test that users page loads Bootstrap"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        # Check for Bootstrap CSS
        bootstrap_links = soup.find_all('link', href=lambda x: x and 'bootstrap' in x.lower())
        assert len(bootstrap_links) > 0
        
        # Check for Bootstrap JS
        bootstrap_scripts = soup.find_all('script', src=lambda x: x and 'bootstrap' in x.lower())
        assert len(bootstrap_scripts) > 0
    
    def test_users_page_has_main_js(self, logged_in_admin):
        """Test that users page includes main.js"""
        response = logged_in_admin.get('/users')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        main_js = soup.find('script', src=lambda x: x and 'main.js' in x)
        assert main_js is not None
