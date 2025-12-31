from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import User, Account, Transaction, Lock
from web.utils import format_number, format_date, calculate_stats

# Get the directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.getenv('WEB_SECRET_KEY', 'change-this-secret-key-in-production-12345')

# Initialize database
db_manager = DatabaseManager()


@app.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Dashboard with statistics"""
    try:
        stats = calculate_stats(db_manager)
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in dashboard route: {e}", exc_info=True)
        return f"خطا در بارگذاری داشبورد: {str(e)}", 500


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    stats = calculate_stats(db_manager)
    return jsonify(stats)


@app.route('/users')
def users():
    """Users management page"""
    return render_template('users.html')


@app.route('/api/users')
def api_users():
    """API endpoint for users list"""
    session = db_manager.get_session()
    try:
        users_list = session.query(User).order_by(User.created_at.desc()).all()
        result = []
        for user in users_list:
            # Get accounts
            accounts = db_manager.get_user_accounts(user.user_id)
            account_count = len(accounts)
            active_account = db_manager.get_active_account(user.user_id)
            balance = float(active_account.balance) if active_account else 0.0
            
            # Check lock status
            lock_info = db_manager.get_lock_info(user.user_id)
            is_locked = lock_info is not None and datetime.utcnow() < lock_info.locked_until if lock_info else False
            
            result.append({
                'user_id': user.user_id,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'account_count': account_count,
                'balance': balance,
                'is_locked': is_locked,
                'lock_reason': lock_info.reason if lock_info else None,
                'lock_until': lock_info.locked_until.isoformat() if lock_info and lock_info.locked_until else None
            })
        return jsonify({'users': result})
    finally:
        session.close()


@app.route('/api/users/<user_id>/lock', methods=['POST'])
def api_lock_user(user_id):
    """Lock a user"""
    reason = request.json.get('reason', 'قفل دستی توسط ادمین')
    db_manager.lock_user(user_id, reason)
    return jsonify({'success': True, 'message': 'کاربر قفل شد'})


@app.route('/api/users/<user_id>/unlock', methods=['POST'])
def api_unlock_user(user_id):
    """Unlock a user"""
    db_manager.unlock_user(user_id)
    return jsonify({'success': True, 'message': 'کاربر باز شد'})


@app.route('/api/users/<user_id>')
def api_user_detail(user_id):
    """Get user details"""
    session = db_manager.get_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        accounts = db_manager.get_user_accounts(user_id)
        accounts_data = []
        for account in accounts:
            transactions = db_manager.get_account_transactions(account.account_number, limit=100)
            accounts_data.append({
                'account_number': account.account_number,
                'balance': float(account.balance),
                'is_active': account.is_active,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'transaction_count': len(transactions)
            })
        
        lock_info = db_manager.get_lock_info(user_id)
        
        return jsonify({
            'user_id': user.user_id,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'accounts': accounts_data,
            'lock': {
                'is_locked': lock_info is not None and datetime.utcnow() < lock_info.locked_until if lock_info else False,
                'reason': lock_info.reason if lock_info else None,
                'locked_until': lock_info.locked_until.isoformat() if lock_info and lock_info.locked_until else None
            } if lock_info else None
        })
    finally:
        session.close()


@app.route('/accounts')
def accounts():
    """Accounts management page"""
    return render_template('accounts.html')


@app.route('/api/accounts')
def api_accounts():
    """API endpoint for accounts list"""
    session = db_manager.get_session()
    try:
        accounts_list = session.query(Account).order_by(Account.created_at.desc()).all()
        result = []
        for account in accounts_list:
            # Get transaction count
            transactions = db_manager.get_account_transactions(account.account_number, limit=1)
            transaction_count = len(transactions)
            
            result.append({
                'account_number': account.account_number,
                'user_id': account.user_id,
                'balance': float(account.balance),
                'is_active': account.is_active,
                'created_at': account.created_at.isoformat() if account.created_at else None
            })
        return jsonify({'accounts': result})
    finally:
        session.close()


@app.route('/api/accounts/<account_number>/toggle', methods=['POST'])
def api_toggle_account(account_number):
    """Activate/Deactivate an account"""
    session = db_manager.get_session()
    try:
        account = session.query(Account).filter(Account.account_number == account_number).first()
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        account.is_active = not account.is_active
        session.commit()
        
        status = 'فعال' if account.is_active else 'غیرفعال'
        return jsonify({'success': True, 'message': f'حساب {status} شد', 'is_active': account.is_active})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/transactions')
def transactions():
    """Transactions management page"""
    return render_template('transactions.html')


@app.route('/api/transactions')
def api_transactions():
    """API endpoint for transactions list"""
    session = db_manager.get_session()
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        account_number = request.args.get('account', None)
        transaction_type = request.args.get('type', None)
        status = request.args.get('status', None)
        
        query = session.query(Transaction)
        
        if account_number:
            query = query.filter(
                (Transaction.from_account == account_number) | 
                (Transaction.to_account == account_number)
            )
        
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        if status:
            query = query.filter(Transaction.status == status)
        
        transactions_list = query.order_by(Transaction.created_at.desc()).limit(limit).all()
        
        result = []
        for trans in transactions_list:
            result.append({
                'id': trans.id,
                'from_account': trans.from_account,
                'to_account': trans.to_account,
                'amount': float(trans.amount),
                'fee': float(trans.fee),
                'transaction_type': trans.transaction_type,
                'status': trans.status,
                'created_at': trans.created_at.isoformat() if trans.created_at else None
            })
        
        return jsonify({'transactions': result})
    finally:
        session.close()


def create_app():
    """Create and configure the Flask app"""
    return app


if __name__ == '__main__':
    print("="*60)
    print("پنل مدیریت وب در حال راه‌اندازی...")
    print("="*60)
    print("\nدسترسی به پنل:")
    print("  http://localhost:5000")
    print("\n" + "="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
