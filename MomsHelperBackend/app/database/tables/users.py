import bcrypt
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from app.database.connection import get_db, JSONDatabase


class User:
    COLLECTION = "users"

    @staticmethod
    def _get_db() -> JSONDatabase:
        return next(get_db())

    @staticmethod
    def find_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        db = User._get_db()
        return db.find_one(User.COLLECTION, lambda u: u["id"] == user_id)

    @staticmethod
    def find_by_username(username: str) -> Optional[Dict[str, Any]]:
        db = User._get_db()
        return db.find_one(User.COLLECTION, lambda u: u["username"] == username)

    @staticmethod
    def find_all() -> List[Dict[str, Any]]:
        db = User._get_db()
        return db.find(User.COLLECTION)

    @staticmethod
    def create(user_data: Dict[str, Any]) -> Dict[str, Any]:
        db = User._get_db()

        moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(moscow_tz).isoformat()

        password = user_data["password"]
        hashed_password = User.hash_password(password)

        user = {
            "username": user_data["username"],
            "lastName": user_data["lastName"],
            "firstName": user_data["firstName"],
            "middleName": user_data["middleName"],
            "hashed_password": hashed_password,
            "is_active": True,
            "is_superuser": user_data.get("is_superuser", False),
            "role_id": user_data.get("role_id"),
            "is_temporary_password": False,
            "created_at": now,
            "last_login": None,
            "last_activity": None,
            "password_changed_at": now
        }

        return db.insert(User.COLLECTION, user)

    @staticmethod
    def update(user_id: str, update_data: Dict[str, Any]) -> int:
        db = User._get_db()
        return db.update(
            User.COLLECTION,
            lambda u: u["id"] == user_id,
            lambda u: u.update(update_data)
        )

    @staticmethod
    def change_password(user_id: str, new_password: str) -> None:
        moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(moscow_tz).isoformat()

        hashed_password = User.hash_password(new_password)

        User.update(user_id, {
            "hashed_password": hashed_password,
            "is_temporary_password": False,
            "password_changed_at": now
        })

    @staticmethod
    def update_last_login(user_id: str) -> None:
        moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(moscow_tz).isoformat()
        User.update(user_id, {"last_login": now, "last_activity": now})

    @staticmethod
    def update_last_activity(user_id: str) -> None:
        moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(moscow_tz).isoformat()
        User.update(user_id, {"last_activity": now})

    @staticmethod
    def count() -> int:
        db = User._get_db()
        return db.count(User.COLLECTION)

    @staticmethod
    def hash_password(password: str) -> str:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
