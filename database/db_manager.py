from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timedelta
from typing import Optional, List
import config
from database.models import Base, User, Account, Transaction, Lock
import bcrypt
import logging
import sys

logger = logging.getLogger(__name__)

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class DatabaseManager:
    def __init__(self):
        # Try to connect to the configured database
        db_url = config.DATABASE_URL
        
        # If PostgreSQL is configured but not available, fallback to SQLite
        if db_url.startswith('postgresql://'):
            try:
                logger.info(f"Attempting to connect to PostgreSQL: {db_url.split('@')[-1] if '@' in db_url else 'database'}")
                self.engine = create_engine(db_url, echo=False)
                self.SessionLocal = sessionmaker(bind=self.engine)
                
                # Test connection
                with self.engine.connect() as conn:
                    pass
                
                # Create tables
                Base.metadata.create_all(self.engine)
                logger.info("PostgreSQL connection successful!")
                return
            except (OperationalError, Exception) as e:
                error_msg = str(e)
                logger.warning(f"PostgreSQL connection failed: {error_msg}")
                logger.info("Falling back to SQLite database...")
                print("\n[WARNING] PostgreSQL is not available. Using SQLite instead.")
                print("For production, please install and configure PostgreSQL.")
                # Fall through to SQLite setup
        
        # Use SQLite (either configured or as fallback)
        if db_url.startswith('sqlite://') or not db_url.startswith('postgresql://'):
            db_url = 'sqlite:///balancebot.db'
            logger.info("Using SQLite database: balancebot.db")
        
        try:
            self.engine = create_engine(db_url, echo=False)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                pass
            
            # Create tables
            Base.metadata.create_all(self.engine)
            logger.info("Database connection successful!")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            print("\n" + "="*60)
            print("Database connection error!")
            print("="*60)
            print(f"\nError: {e}")
            print("\nPlease check:")
            print("1. If using PostgreSQL: ensure it's installed and running")
            print("2. Check DATABASE_URL in .env file")
            print("3. Ensure you have write permissions for SQLite file")
            print("\n" + "="*60)
            raise
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    # User operations
    def get_or_create_user(self, user_id: str) -> User:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            if not user:
                user = User(user_id=str(user_id))
                session.add(user)
                session.commit()
                session.refresh(user)
            return user
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_user_state(self, user_id: str, encrypted_state: str):
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            if user:
                user.encrypted_state = encrypted_state
                user.updated_at = datetime.utcnow()
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_state(self, user_id: str) -> Optional[str]:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            return user.encrypted_state if user else None
        finally:
            session.close()
    
    # Account operations
    def create_account(self, user_id: str, account_number: str, password: str) -> Account:
        session = self.get_session()
        try:
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            account = Account(
                account_number=account_number,
                user_id=str(user_id),
                password_hash=password_hash,
                balance=0.00,
                is_active=True
            )
            session.add(account)
            session.commit()
            session.refresh(account)
            return account
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_account_by_number(self, account_number: str) -> Optional[Account]:
        session = self.get_session()
        try:
            return session.query(Account).filter(Account.account_number == account_number).first()
        finally:
            session.close()
    
    def get_user_accounts(self, user_id: str) -> List[Account]:
        session = self.get_session()
        try:
            return session.query(Account).filter(
                Account.user_id == str(user_id),
                Account.is_active == True
            ).all()
        finally:
            session.close()
    
    def get_active_account(self, user_id: str) -> Optional[Account]:
        session = self.get_session()
        try:
            return session.query(Account).filter(
                Account.user_id == str(user_id),
                Account.is_active == True
            ).first()
        finally:
            session.close()
    
    def verify_password(self, account_number: str, password: str) -> bool:
        session = self.get_session()
        try:
            account = session.query(Account).filter(Account.account_number == account_number).first()
            if account:
                return bcrypt.checkpw(password.encode(), account.password_hash.encode())
            return False
        finally:
            session.close()
    
    def update_account_balance(self, account_number: str, amount: float):
        session = self.get_session()
        try:
            account = session.query(Account).filter(Account.account_number == account_number).first()
            if account:
                account.balance += amount
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_account_user_and_activate(self, account_number: str, user_id: str):
        """Update account user_id and activate it (for recovery)"""
        session = self.get_session()
        try:
            account = session.query(Account).filter(Account.account_number == account_number).first()
            if account:
                account.user_id = str(user_id)
                account.is_active = True
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_account_balance(self, account_number: str) -> float:
        session = self.get_session()
        try:
            account = session.query(Account).filter(Account.account_number == account_number).first()
            return float(account.balance) if account else 0.0
        finally:
            session.close()
    
    def account_exists(self, account_number: str) -> bool:
        session = self.get_session()
        try:
            return session.query(Account).filter(Account.account_number == account_number).first() is not None
        finally:
            session.close()
    
    # Transaction operations
    def create_transaction(self, from_account: Optional[str], to_account: Optional[str], 
                          amount: float, fee: float, transaction_type: str) -> Transaction:
        session = self.get_session()
        try:
            transaction = Transaction(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                fee=fee,
                transaction_type=transaction_type,
                status='pending'
            )
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_transaction_status(self, transaction_id: int, status: str):
        session = self.get_session()
        try:
            transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
            if transaction:
                transaction.status = status
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_account_transactions(self, account_number: str, limit: int = 10) -> List[Transaction]:
        session = self.get_session()
        try:
            return session.query(Transaction).filter(
                (Transaction.from_account == account_number) | 
                (Transaction.to_account == account_number)
            ).order_by(Transaction.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    # Lock operations
    def lock_user(self, user_id: str, reason: str = None):
        session = self.get_session()
        try:
            locked_until = datetime.utcnow() + timedelta(minutes=config.LOCK_DURATION_MINUTES)
            lock = session.query(Lock).filter(Lock.user_id == str(user_id)).first()
            if lock:
                lock.locked_until = locked_until
                lock.reason = reason
            else:
                lock = Lock(user_id=str(user_id), locked_until=locked_until, reason=reason)
                session.add(lock)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def is_user_locked(self, user_id: str) -> bool:
        session = self.get_session()
        try:
            lock = session.query(Lock).filter(Lock.user_id == str(user_id)).first()
            if lock:
                return datetime.utcnow() < lock.locked_until
            return False
        finally:
            session.close()
    
    def unlock_user(self, user_id: str):
        session = self.get_session()
        try:
            lock = session.query(Lock).filter(Lock.user_id == str(user_id)).first()
            if lock:
                session.delete(lock)
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_lock_info(self, user_id: str) -> Optional[Lock]:
        session = self.get_session()
        try:
            return session.query(Lock).filter(Lock.user_id == str(user_id)).first()
        finally:
            session.close()

