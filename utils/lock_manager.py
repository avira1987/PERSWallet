from datetime import datetime
from typing import Tuple
from database.db_manager import DatabaseManager
import config


class LockManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def check_lock(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user is locked
        Returns: (is_locked, message)
        """
        if self.db.is_user_locked(user_id):
            lock_info = self.db.get_lock_info(user_id)
            if lock_info:
                remaining = lock_info.locked_until - datetime.utcnow()
                minutes = int(remaining.total_seconds() / 60)
                seconds = int(remaining.total_seconds() % 60)
                return True, f"اکانت شما به مدت {minutes} دقیقه و {seconds} ثانیه قفل شده است. لطفا صبر کنید."
        return False, ""
    
    def lock_user(self, user_id: str, reason: str = "تعداد تلاش‌های ناموفق بیش از حد"):
        """
        Lock user for 10 minutes
        """
        self.db.lock_user(user_id, reason)
    
    def unlock_user(self, user_id: str):
        """
        Unlock user
        """
        self.db.unlock_user(user_id)

