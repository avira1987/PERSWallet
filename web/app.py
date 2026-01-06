from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from functools import wraps
import os
import sys
import json
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import User, Account, Transaction, Lock, WithdrawalRequest
import config
from web.utils import format_number, format_date, calculate_stats
from web.auth import login_manager, WebUser
from sqlalchemy import func, or_, case
from sqlalchemy.orm import joinedload

# Get the directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Security: Use secret key from config (required for web interface)
if not config.WEB_SECRET_KEY:
    import sys
    print("ERROR: WEB_SECRET_KEY environment variable is required for web interface!")
    print("Please set WEB_SECRET_KEY in your .env file.")
    print("Generate a secure key using: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
    sys.exit(1)
app.secret_key = config.WEB_SECRET_KEY

# CSRF Protection
csrf = CSRFProtect(app)

# Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize database
db_manager = DatabaseManager()

# Setup Flask-Login
login_manager.init_app(app)
login_manager.db_manager = db_manager

# Set db_manager for user loader
from web.auth import load_user as auth_load_user
auth_load_user.db_manager = db_manager

logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - simple authentication using admin user_id"""
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        
        if not user_id:
            flash('لطفا شناسه کاربری را وارد کنید.', 'error')
            return render_template('login.html'), 401
        
        # Check if user exists and is admin
        if db_manager.is_admin(user_id):
            user = WebUser.get(user_id, db_manager)
            if user:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        
        flash('شناسه کاربری یا سطح دسترسی نامعتبر است.', 'error')
        return render_template('login.html'), 401
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('با موفقیت خارج شدید.', 'info')
    return redirect(url_for('login'))


@app.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard with statistics"""
    try:
        stats = calculate_stats(db_manager)
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Error in dashboard route: {e}", exc_info=True)
        flash('خطا در بارگذاری داشبورد. لطفا دوباره تلاش کنید.', 'error')
        return render_template('dashboard.html', stats={}), 500


@app.route('/api/stats')
@login_required
@admin_required
@limiter.limit("30 per minute")
def api_stats():
    """API endpoint for statistics"""
    stats = calculate_stats(db_manager)
    return jsonify(stats)


@app.route('/users')
@login_required
@admin_required
def users():
    """Users management page"""
    return render_template('users.html')


@app.route('/api/users')
@login_required
@admin_required
@limiter.limit("60 per minute")
def api_users():
    """API endpoint for users list - optimized with SQL aggregation"""
    db_session = db_manager.get_session()
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        per_page = min(per_page, 500)  # Limit max per_page to prevent abuse
        
        # Use SQL aggregation to calculate account count and balance efficiently
        # This avoids loading all accounts into memory
        
        # Subquery for account statistics per user
        account_stats = db_session.query(
            Account.user_id,
            func.count(Account.account_number).label('account_count'),
            func.max(
                case(
                    (Account.is_active == True, Account.balance),
                    else_=None
                )
            ).label('active_balance')
        ).group_by(Account.user_id).subquery()
        
        # Main query with left join for locks and account stats
        query = db_session.query(
            User,
            Lock,
            account_stats.c.account_count,
            account_stats.c.active_balance
        ).outerjoin(
            Lock, User.user_id == Lock.user_id
        ).outerjoin(
            account_stats, User.user_id == account_stats.c.user_id
        ).order_by(User.created_at.desc())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        users_data = query.offset((page - 1) * per_page).limit(per_page).all()
        
        now = datetime.utcnow()
        result = []
        for user, lock_info, account_count, active_balance in users_data:
            # Check if user is locked
            is_locked = lock_info is not None and now < lock_info.locked_until if lock_info else False
            
            result.append({
                'user_id': user.user_id,
                'username': user.username if user.username else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'account_count': account_count if account_count else 0,
                'balance': float(active_balance) if active_balance is not None else 0.0,
                'is_locked': is_locked,
                'lock_reason': lock_info.reason if lock_info else None,
                'lock_until': lock_info.locked_until.isoformat() if lock_info and lock_info.locked_until else None,
                'is_admin': user.is_admin if user.is_admin else False
            })
        
        return jsonify({
            'users': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page if total_count > 0 else 0
            }
        })
    except Exception as e:
        logger.error(f"Error in api_users: {e}", exc_info=True)
        return jsonify({'error': 'خطا در بارگذاری کاربران', 'details': str(e)}), 500
    finally:
        db_session.close()


@app.route('/api/users/<user_id>/lock', methods=['POST'])
@login_required
@admin_required
@limiter.limit("20 per minute")
def api_lock_user(user_id):
    """Lock a user"""
    reason = request.json.get('reason', 'قفل دستی توسط ادمین')
    db_manager.lock_user(user_id, reason)
    return jsonify({'success': True, 'message': 'کاربر قفل شد'})


@app.route('/api/users/<user_id>/unlock', methods=['POST'])
@login_required
@admin_required
@limiter.limit("20 per minute")
def api_unlock_user(user_id):
    """Unlock a user"""
    db_manager.unlock_user(user_id)
    return jsonify({'success': True, 'message': 'کاربر باز شد'})


@app.route('/api/users/<user_id>/delete', methods=['DELETE'])
@login_required
@admin_required
@limiter.limit("10 per minute")
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
@login_required
@admin_required
@limiter.limit("5 per minute")
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
@login_required
@admin_required
@limiter.limit("60 per minute")
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
@login_required
@admin_required
def accounts():
    """Accounts management page"""
    return render_template('accounts.html')


@app.route('/api/accounts')
@login_required
@admin_required
@limiter.limit("60 per minute")
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
@login_required
@admin_required
@limiter.limit("30 per minute")
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
@login_required
@admin_required
@limiter.limit("30 per minute")
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
@login_required
@admin_required
@limiter.limit("10 per minute")
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
@login_required
@admin_required
def transactions():
    """Transactions management page"""
    return render_template('transactions.html')


@app.route('/tutorial')
@login_required
@admin_required
def tutorial():
    """Tutorial page for using the Telegram bot"""
    return render_template('tutorial.html')


@app.route('/withdrawals')
@login_required
@admin_required
def withdrawals():
    """Withdrawal requests management page"""
    return render_template('withdrawals.html')


@app.route('/api/withdrawals')
@login_required
@admin_required
@limiter.limit("60 per minute")
def api_withdrawals():
    """API endpoint for withdrawal requests list"""
    session = db_manager.get_session()
    try:
        status = request.args.get('status', None)
        withdrawals_list = db_manager.get_withdrawal_requests(status=status, limit=500)
        
        result = []
        for w in withdrawals_list:
            result.append({
                'id': w.id,
                'user_id': w.user_id,
                'account_number': w.account_number,
                'amount_pers': float(w.amount_pers),
                'amount_toman': float(w.amount_toman),
                'sheba': w.sheba,
                'status': w.status,
                'transaction_id': w.transaction_id,
                'confirmed_at': w.confirmed_at.isoformat() if w.confirmed_at else None,
                'confirmed_by': w.confirmed_by,
                'created_at': w.created_at.isoformat() if w.created_at else None
            })
        
        return jsonify({'withdrawals': result})
    except Exception as e:
        logger.error(f"Error in api_withdrawals: {e}", exc_info=True)
        return jsonify({'error': 'خطا در بارگذاری درخواست‌های واریز'}), 500
    finally:
        session.close()


@app.route('/api/withdrawals/<int:request_id>/confirm', methods=['POST'])
@login_required
@admin_required
@limiter.limit("20 per minute")
def api_confirm_withdrawal(request_id):
    """Confirm a withdrawal request and send confirmation message to user"""
    try:
        # Get withdrawal request
        withdrawal = db_manager.get_withdrawal_request(request_id)
        if not withdrawal:
            return jsonify({'error': 'درخواست یافت نشد'}), 404
        
        if withdrawal.status != 'pending':
            return jsonify({'error': 'این درخواست قبلا پردازش شده است'}), 400
        
        # Confirm the withdrawal
        confirmed_by = current_user.id if current_user.is_authenticated else 'admin'
        success = db_manager.confirm_withdrawal_request(request_id, confirmed_by)
        
        if not success:
            return jsonify({'error': 'خطا در تایید درخواست'}), 500
        
        # Send confirmation message to user via Telegram
        try:
            send_telegram_message(
                user_id=withdrawal.user_id,
                message=create_withdrawal_confirmation_message(withdrawal)
            )
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}", exc_info=True)
            # Don't fail the request if message sending fails
        
        # Mark as completed after sending message
        db_manager.complete_withdrawal_request(request_id)
        
        return jsonify({'success': True, 'message': 'درخواست با موفقیت تایید شد و پیام به کاربر ارسال شد'})
    except Exception as e:
        logger.error(f"Error in api_confirm_withdrawal: {e}", exc_info=True)
        return jsonify({'error': 'خطا در پردازش درخواست'}), 500


def send_telegram_message(user_id: str, message: str):
    """Send a Telegram message to a user"""
    try:
        from telegram import Bot
        import asyncio
        
        if not config.BOT_TOKEN:
            raise Exception("BOT_TOKEN is not set")
        
        bot = Bot(token=config.BOT_TOKEN)
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.send_message(chat_id=user_id, text=message))
        loop.close()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending Telegram message to {user_id}: {e}")
        raise


def create_withdrawal_confirmation_message(withdrawal: WithdrawalRequest) -> str:
    """Create confirmation message for withdrawal"""
    message = "✅ واریز ریالی شما انجام شد!\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"💰 مبلغ واریز شده: {float(withdrawal.amount_toman):,.0f} تومان\n"
    message += f"💼 معادل PERS: {float(withdrawal.amount_pers):,.2f} PERS\n"
    message += f"🏦 شماره شبا: {withdrawal.sheba}\n"
    message += f"🆔 شماره درخواست: #{withdrawal.id}\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━\n\n"
    message += "🎉 مبلغ به حساب بانکی شما واریز شده است.\n\n"
    message += "💡 در صورت هرگونه مشکل، با پشتیبانی تماس بگیرید:\n"
    message += "📞 @PERS_coin_bot_support"
    
    return message


@app.route('/api/transactions')
@login_required
@admin_required
@limiter.limit("60 per minute")
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
            # Ensure fee is properly converted from Decimal/None to float
            fee_value = float(trans.fee) if trans.fee is not None else 0.0
            result.append({
                'id': trans.id,
                'from_account': trans.from_account,
                'to_account': trans.to_account,
                'amount': float(trans.amount),
                'fee': fee_value,
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
