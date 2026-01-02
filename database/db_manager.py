from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal
import config
from database.models import Base, User, Account, Transaction, Lock
from utils.encryption import hash_password, verify_password, hash_account_number, verify_account_number
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
                
                # Migrate: Add agreement_accepted column if it doesn't exist
                self._migrate_agreement_column()
                # Migrate: Add is_admin column if it doesn't exist
                self._migrate_is_admin_column()
                # Migrate: Add username column if it doesn't exist
                self._migrate_username_column()
                
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
            
            # Migrate: Add agreement_accepted column if it doesn't exist
            self._migrate_agreement_column()
            # Migrate: Add account_number_hash column if it doesn't exist
            self._migrate_account_number_hash_column()
            # Migrate: Add is_admin column if it doesn't exist
            self._migrate_is_admin_column()
            # Migrate: Add username column if it doesn't exist
            self._migrate_username_column()
            
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
    
    def _migrate_agreement_column(self):
        """Migrate: Add agreement_accepted column to users table if it doesn't exist"""
        try:
            from sqlalchemy import inspect, text
            
            inspector = inspect(self.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'agreement_accepted' not in columns:
                logger.info("Migrating: Adding agreement_accepted column to users table...")
                with self.engine.connect() as conn:
                    # SQLite
                    if 'sqlite' in str(self.engine.url):
                        conn.execute(text("ALTER TABLE users ADD COLUMN agreement_accepted BOOLEAN DEFAULT 0"))
                    # PostgreSQL
                    else:
                        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS agreement_accepted BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                logger.info("Migration completed: agreement_accepted column added")
        except Exception as e:
            logger.warning(f"Migration warning (may already exist): {e}")
    
    def _migrate_account_number_hash_column(self):
        """Migrate: Add account_number_hash column to accounts table if it doesn't exist"""
        try:
            from sqlalchemy import inspect, text
            
            inspector = inspect(self.engine)
            columns = [col['name'] for col in inspector.get_columns('accounts')]
            
            if 'account_number_hash' not in columns:
                logger.info("Migrating: Adding account_number_hash column to accounts table...")
                with self.engine.connect() as conn:
                    # SQLite
                    if 'sqlite' in str(self.engine.url):
                        conn.execute(text("ALTER TABLE accounts ADD COLUMN account_number_hash VARCHAR(255)"))
                    # PostgreSQL
                    else:
                        conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_number_hash VARCHAR(255)"))
                    conn.commit()
                logger.info("Migration completed: account_number_hash column added")
                
                # Backfill existing accounts with hashed account numbers
                logger.info("Backfilling account_number_hash for existing accounts...")
                self._backfill_account_number_hashes()
        except Exception as e:
            logger.warning(f"Migration warning (may already exist): {e}")
    
    def _backfill_account_number_hashes(self):
        """Backfill account_number_hash for existing accounts"""
        try:
            session = self.get_session()
            try:
                accounts = session.query(Account).filter(Account.account_number_hash == None).all()
                updated_count = 0
                for account in accounts:
                    account.account_number_hash = hash_account_number(account.account_number)
                    updated_count += 1
                if updated_count > 0:
                    session.commit()
                    logger.info(f"Backfilled account_number_hash for {updated_count} existing accounts")
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"Backfill warning: {e}")
    
    def _migrate_is_admin_column(self):
        """Migrate: Add is_admin column to users table if it doesn't exist"""
        try:
            from sqlalchemy import inspect, text
            
            inspector = inspect(self.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'is_admin' not in columns:
                logger.info("Migrating: Adding is_admin column to users table...")
                with self.engine.connect() as conn:
                    # SQLite
                    if 'sqlite' in str(self.engine.url):
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                    # PostgreSQL
                    else:
                        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                logger.info("Migration completed: is_admin column added")
        except Exception as e:
            logger.warning(f"Migration warning (may already exist): {e}")
    
    def _migrate_username_column(self):
        """Migrate: Add username column to users table if it doesn't exist"""
        try:
            from sqlalchemy import inspect, text
            
            inspector = inspect(self.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'username' not in columns:
                logger.info("Migrating: Adding username column to users table...")
                with self.engine.connect() as conn:
                    # SQLite
                    if 'sqlite' in str(self.engine.url):
                        conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(255)"))
                    # PostgreSQL
                    else:
                        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(255)"))
                    conn.commit()
                logger.info("Migration completed: username column added")
        except Exception as e:
            logger.warning(f"Migration warning (may already exist): {e}")
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    # User operations
    def get_or_create_user(self, user_id: str, username: str = None) -> User:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            if not user:
                user = User(user_id=str(user_id), username=username)
                session.add(user)
                session.commit()
                session.refresh(user)
            elif username and user.username != username:
                # Update username if it has changed
                user.username = username
                user.updated_at = datetime.utcnow()
                session.commit()
            return user
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_user_username(self, user_id: str, username: str):
        """Update user's username"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            if user:
                user.username = username
                user.updated_at = datetime.utcnow()
                session.commit()
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
    
    def has_accepted_agreement(self, user_id: str) -> bool:
        """Check if user has accepted the agreement"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            return user.agreement_accepted if user else False
        finally:
            session.close()
    
    def accept_agreement(self, user_id: str):
        """Mark user as having accepted the agreement"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            if user:
                user.agreement_accepted = True
                user.updated_at = datetime.utcnow()
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # Account operations
    def create_account(self, user_id: str, account_number: str, password: str) -> Account:
        session = self.get_session()
        try:
            # Check if account already exists
            existing_account = session.query(Account).filter(Account.account_number == account_number).first()
            if existing_account:
                logger.warning(f"Account {account_number} already exists, returning existing account")
                return existing_account
            
            password_hash = hash_password(password)
            account_number_hash = hash_account_number(account_number)
            account = Account(
                account_number=account_number,
                user_id=str(user_id),
                password_hash=password_hash,
                account_number_hash=account_number_hash,
                balance=0.00,
                is_active=True
            )
            session.add(account)
            session.commit()
            session.refresh(account)
            return account
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating account {account_number}: {e}")
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
                return verify_password(account.password_hash, password)
            return False
        finally:
            session.close()
    
    def update_account_balance(self, account_number: str, amount: float):
        session = self.get_session()
        try:
            account = session.query(Account).filter(Account.account_number == account_number).first()
            if account:
                # Convert amount to Decimal to match database type
                amount_decimal = Decimal(str(amount))
                account.balance = Decimal(str(account.balance)) + amount_decimal
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def set_account_balance(self, account_number: str, balance: float):
        """Set account balance to a specific value"""
        session = self.get_session()
        try:
            account = session.query(Account).filter(Account.account_number == account_number).first()
            if account:
                # Convert balance to Decimal to match database type
                account.balance = Decimal(str(balance))
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def reset_account_password(self, account_number: str, new_password: str):
        """Reset account password"""
        session = self.get_session()
        try:
            account = session.query(Account).filter(Account.account_number == account_number).first()
            if account:
                password_hash = hash_password(new_password)
                account.password_hash = password_hash
                session.commit()
                return True
            return False
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
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user and all associated data (accounts, locks, transactions)"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            if not user:
                return False
            
            # Delete associated locks
            lock = session.query(Lock).filter(Lock.user_id == str(user_id)).first()
            if lock:
                session.delete(lock)
            
            # Delete associated accounts (and their transactions will be handled by cascade or manually)
            accounts = session.query(Account).filter(Account.user_id == str(user_id)).all()
            for account in accounts:
                # Delete transactions associated with this account
                session.query(Transaction).filter(
                    (Transaction.from_account == account.account_number) |
                    (Transaction.to_account == account.account_number)
                ).delete()
                session.delete(account)
            
            # Delete the user
            session.delete(user)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            raise e
        finally:
            session.close()
    
    def set_admin_status(self, user_id: str, is_admin: bool) -> bool:
        """Set admin status for a user"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            if not user:
                return False
            
            user.is_admin = is_admin
            user.updated_at = datetime.utcnow()
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error setting admin status for user {user_id}: {e}")
            raise e
        finally:
            session.close()
    
    def is_admin(self, user_id: str) -> bool:
        """Check if a user is an admin"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.user_id == str(user_id)).first()
            return user.is_admin if user else False
        finally:
            session.close()

