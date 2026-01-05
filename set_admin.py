#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to set a user as admin for web panel access
Usage: python set_admin.py <user_id>
"""

import sys
from database.db_manager import DatabaseManager
from database.models import User

def main():
    if len(sys.argv) < 2:
        print("Usage: python set_admin.py <user_id>")
        print("Example: python set_admin.py 332935318")
        sys.exit(1)
    
    user_id = sys.argv[1].strip()
    
    print(f"Setting user {user_id} as admin...")
    
    db = DatabaseManager()
    
    # Check if user exists
    session = db.get_session()
    try:
        user = session.query(User).filter(User.user_id == str(user_id)).first()
        if not user:
            print(f"\n❌ Error: User {user_id} not found in database!")
            print("Please use the bot first to create an account (send /start to the bot).")
            sys.exit(1)
        
        print(f"✓ User found: {user.user_id}")
        if user.username:
            print(f"  Username: {user.username}")
        
    finally:
        session.close()
    
    # Set as admin
    try:
        success = db.set_admin_status(user_id, True)
        if success:
            print(f"\n✅ Success! User {user_id} is now an admin.")
            print(f"\nYou can now login to the web panel:")
            print(f"  URL: http://localhost:5000/login")
            print(f"  User ID: {user_id}")
        else:
            print(f"\n❌ Error: Failed to set user {user_id} as admin")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
