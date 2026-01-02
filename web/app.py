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
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

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
    """API endpoint for users list - optimized with joins"""
    db_session = db_manager.get_session()
    try:
        # Get all users with eager loading of accounts and locks
        users_list = db_session.query(User).options(
            joinedload(User.accounts),
            joinedload(User.lock)
        ).order_by(User.created_at.desc()).all()
        
        # Pre-load all locks in one query
        user_ids = [user.user_id for user in users_list]
        locks = db_session.query(Lock).filter(Lock.user_id.in_(user_ids)).all()
        locks_dict = {lock.user_id: lock for lock in locks}
        
        now = datetime.utcnow()
        result = []
        for user in users_list:
            # Use eager-loaded accounts to calculate stats (no extra queries)
            accounts = user.accounts if user.accounts else []
            account_count = len(accounts)
            
            # Find active account balance
            balance = 0.0
            for acc in accounts:
                if acc.is_active:
                    balance = float(acc.balance)
                    break  # Use first active account
            
            # Get lock info from eager-loaded or dict
            lock_info = user.lock if hasattr(user, 'lock') and user.lock else locks_dict.get(user.user_id)
            is_locked = lock_info is not None and now < lock_info.locked_until if lock_info else False
            
            result.append({
                'user_id': user.user_id,
                'username': user.username if user.username else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'account_count': account_count,
                'balance': balance,
                'is_locked': is_locked,
                'lock_reason': lock_info.reason if lock_info else None,
                'lock_until': lock_info.locked_until.isoformat() if lock_info and lock_info.locked_until else None,
                'is_admin': user.is_admin if user.is_admin else False
            })
        return jsonify({'users': result})
    finally:
        db_session.close()


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


@app.route('/api/users/<user_id>/delete', methods=['DELETE'])
def api_delete_user(user_id):
    """Delete a user"""
    try:
        success = db_manager.delete_user(user_id)
        if success:
            return jsonify({'success': True, 'message': 'کاربر با موفقیت حذف شد'})
        else:
            return jsonify({'error': 'کاربر یافت نشد'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>/admin', methods=['POST'])
def api_set_admin_status(user_id):
    """Set admin status for a user"""
    try:
        data = request.json
        is_admin = data.get('is_admin', False)
        success = db_manager.set_admin_status(user_id, is_admin)
        if success:
            status_text = 'ادمین' if is_admin else 'کاربر عادی'
            return jsonify({'success': True, 'message': f'کاربر به {status_text} تبدیل شد'})
        else:
            return jsonify({'error': 'کاربر یافت نشد'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>')
def api_user_detail(user_id):
    """Get user details - optimized"""
    db_session = db_manager.get_session()
    try:
        # Load user with accounts in one query
        user = db_session.query(User).options(
            joinedload(User.accounts),
            joinedload(User.lock)
        ).filter(User.user_id == user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all account numbers for this user
        account_numbers = [acc.account_number for acc in user.accounts] if user.accounts else []
        
        # Count transactions for all accounts in one query
        transaction_counts = {}
        if account_numbers:
            from_counts = db_session.query(
                Transaction.from_account,
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.from_account.in_(account_numbers)
            ).group_by(Transaction.from_account).all()
            
            to_counts = db_session.query(
                Transaction.to_account,
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.to_account.in_(account_numbers)
            ).group_by(Transaction.to_account).all()
            
            # Merge counts
            for acc_num, count in from_counts:
                transaction_counts[acc_num] = transaction_counts.get(acc_num, 0) + count
            for acc_num, count in to_counts:
                transaction_counts[acc_num] = transaction_counts.get(acc_num, 0) + count
        
        accounts_data = []
        for account in user.accounts:
            accounts_data.append({
                'account_number': account.account_number,
                'balance': float(account.balance),
                'is_active': account.is_active,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'transaction_count': transaction_counts.get(account.account_number, 0)
            })
        
        lock_info = user.lock if hasattr(user, 'lock') else None
        now = datetime.utcnow()
        
        return jsonify({
            'user_id': user.user_id,
            'username': user.username if user.username else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'is_admin': user.is_admin if user.is_admin else False,
            'accounts': accounts_data,
            'lock': {
                'is_locked': lock_info is not None and now < lock_info.locked_until if lock_info else False,
                'reason': lock_info.reason if lock_info else None,
                'locked_until': lock_info.locked_until.isoformat() if lock_info and lock_info.locked_until else None
            } if lock_info else None
        })
    finally:
        db_session.close()


@app.route('/accounts')
def accounts():
    """Accounts management page"""
    return render_template('accounts.html')


@app.route('/api/accounts')
def api_accounts():
    """API endpoint for accounts list - optimized (removed unnecessary transaction count)"""
    db_session = db_manager.get_session()
    try:
        # Get all accounts except admin/system accounts with user info
        # Note: Removed transaction count query as it was causing performance issues
        # and the count wasn't being displayed in the UI anyway
        accounts_list = db_session.query(Account).options(
            joinedload(Account.user)
        ).filter(
            Account.user_id != "admin",
            Account.account_number != "0000000000000001"
        ).order_by(Account.created_at.desc()).all()
        
        result = []
        for account in accounts_list:
            result.append({
                'account_number': account.account_number,
                'user_id': account.user_id,
                'username': account.user.username if account.user and account.user.username else None,
                'balance': float(account.balance),
                'is_active': account.is_active,
                'created_at': account.created_at.isoformat() if account.created_at else None
            })
        return jsonify({'accounts': result})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in api_accounts: {e}", exc_info=True)
        return jsonify({'error': 'خطا در بارگذاری حساب‌ها', 'details': str(e)}), 500
    finally:
        db_session.close()


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


@app.route('/api/accounts/<account_number>/balance', methods=['POST'])
def api_update_account_balance(account_number):
    """Update account balance (increase/decrease)"""
    try:
        data = request.json
        amount = float(data.get('amount', 0))
        action = data.get('action', 'add')  # 'add' or 'set'
        
        if action == 'set':
            balance = float(data.get('balance', 0))
            db_manager.set_account_balance(account_number, balance)
            return jsonify({'success': True, 'message': f'موجودی حساب به {balance:,.2f} PERS تنظیم شد'})
        else:
            db_manager.update_account_balance(account_number, amount)
            action_text = 'افزایش' if amount > 0 else 'کاهش'
            return jsonify({'success': True, 'message': f'{action_text} موجودی با موفقیت انجام شد'})
    except ValueError:
        return jsonify({'error': 'مقدار نامعتبر'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/<account_number>/reset-password', methods=['POST'])
def api_reset_account_password(account_number):
    """Reset account password"""
    try:
        data = request.json
        new_password = data.get('password', '')
        
        if not new_password or len(new_password) != 8 or not new_password.isdigit():
            return jsonify({'error': 'رمز عبور باید ۸ رقم عددی باشد'}), 400
        
        success = db_manager.reset_account_password(account_number, new_password)
        if success:
            return jsonify({'success': True, 'message': 'رمز عبور با موفقیت تغییر یافت'})
        else:
            return jsonify({'error': 'حساب یافت نشد'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/transactions')
def transactions():
    """Transactions management page"""
    return render_template('transactions.html')


@app.route('/tutorial')
def tutorial():
    """Tutorial page for using the Telegram bot"""
    return render_template('tutorial.html')


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
    import socket
    # Get local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("="*60)
    print("پنل مدیریت وب در حال راه‌اندازی...")
    print("="*60)
    print("\nدسترسی به پنل:")
    print(f"  http://localhost:5000")
    print(f"  http://{local_ip}:5000")
    print("\nبرای دسترسی از اینترنت:")
    print("  از IP عمومی سرور خود استفاده کنید")
    print("  مطمئن شوید پورت 5000 در فایروال باز است")
    print("\n" + "="*60 + "\n")
    app.run(debug=False, host='0.0.0.0', port=5000)
