from datetime import datetime, timedelta
from database.models import User, Account, Transaction, Lock
import logging

logger = logging.getLogger(__name__)


def format_number(number):
    """Format number with thousand separators"""
    return f"{number:,.2f}"


def format_date(date_obj):
    """Format datetime object to Persian-friendly string"""
    if not date_obj:
        return '-'
    if isinstance(date_obj, str):
        date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
    return date_obj.strftime('%Y-%m-%d %H:%M:%S')


def calculate_stats(db_manager):
    """Calculate statistics for dashboard"""
    session = db_manager.get_session()
    try:
        # Total users
        total_users = session.query(User).count()
        
        # Total accounts
        total_accounts = session.query(Account).count()
        active_accounts = session.query(Account).filter(Account.is_active == True).count()
        
        # Total transactions
        total_transactions = session.query(Transaction).count()
        pending_transactions = session.query(Transaction).filter(Transaction.status == 'pending').count()
        success_transactions = session.query(Transaction).filter(Transaction.status == 'success').count()
        
        # Total balance
        accounts = session.query(Account).all()
        total_balance = sum(float(acc.balance) if acc.balance is not None else 0.0 for acc in accounts)
        
        # Transactions by type
        buy_count = session.query(Transaction).filter(Transaction.transaction_type == 'buy').count()
        sell_count = session.query(Transaction).filter(Transaction.transaction_type == 'sell').count()
        send_count = session.query(Transaction).filter(Transaction.transaction_type == 'send').count()
        
        # Recent transactions (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_transactions = session.query(Transaction).filter(
            Transaction.created_at >= yesterday
        ).count()
        
        # Locked users
        locked_users = session.query(Lock).filter(
            Lock.locked_until > datetime.utcnow()
        ).count()
        
        return {
            'total_users': total_users,
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'total_transactions': total_transactions,
            'pending_transactions': pending_transactions,
            'success_transactions': success_transactions,
            'total_balance': total_balance,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'send_count': send_count,
            'recent_transactions': recent_transactions,
            'locked_users': locked_users
        }
    except Exception as e:
        logger.error(f"Error calculating stats: {e}", exc_info=True)
        # Return default values on error
        return {
            'total_users': 0,
            'total_accounts': 0,
            'active_accounts': 0,
            'total_transactions': 0,
            'pending_transactions': 0,
            'success_transactions': 0,
            'total_balance': 0.0,
            'buy_count': 0,
            'sell_count': 0,
            'send_count': 0,
            'recent_transactions': 0,
            'locked_users': 0
        }
    finally:
        session.close()
