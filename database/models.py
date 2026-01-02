from sqlalchemy import create_engine, Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String(50), primary_key=True)
    username = Column(String(255), nullable=True)
    encrypted_state = Column(Text, nullable=True)
    agreement_accepted = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    accounts = relationship("Account", back_populates="user")
    lock = relationship("Lock", back_populates="user", uselist=False)


class Account(Base):
    __tablename__ = 'accounts'
    
    account_number = Column(String(16), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=False)
    password_hash = Column(String(255), nullable=False)
    account_number_hash = Column(String(255), nullable=True)
    balance = Column(Numeric(20, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="accounts")
    transactions_from = relationship("Transaction", foreign_keys="Transaction.from_account", back_populates="from_account_rel")
    transactions_to = relationship("Transaction", foreign_keys="Transaction.to_account", back_populates="to_account_rel")


class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_account = Column(String(16), ForeignKey('accounts.account_number'), nullable=True)
    to_account = Column(String(16), ForeignKey('accounts.account_number'), nullable=True)
    amount = Column(Numeric(20, 2), nullable=False)
    fee = Column(Numeric(20, 2), default=0.00)
    transaction_type = Column(String(20), nullable=False)  # buy, send, sell
    status = Column(String(20), default='pending')  # pending, success, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    from_account_rel = relationship("Account", foreign_keys=[from_account], back_populates="transactions_from")
    to_account_rel = relationship("Account", foreign_keys=[to_account], back_populates="transactions_to")


class Lock(Base):
    __tablename__ = 'locks'
    
    user_id = Column(String(50), ForeignKey('users.user_id'), primary_key=True)
    locked_until = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=True)
    
    user = relationship("User", back_populates="lock")

