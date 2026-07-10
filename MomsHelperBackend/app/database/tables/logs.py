from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from app.database.connection import get_db, JSONDatabase


class Log:
    collection = "logs"

    @staticmethod
    def _get_db() -> JSONDatabase:
        return next(get_db())

    @staticmethod
    def create(level: str, log_type: str, message: str,
               user_id: Optional[str] = None,
               username: Optional[str] = None,
               ip_address: Optional[str] = None) -> Dict[str, Any]:
        db = Log._get_db()

        moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(moscow_tz).isoformat()

        log = {
            "level": level.lower(),
            "log_type": log_type.lower(),
            "message": message,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "created_at": now
        }

        return db.insert(Log.collection, log)

    @staticmethod
    def find_all(skip: int = 0, limit: int = None) -> List[Dict[str, Any]]:
        db = Log._get_db()
        logs = db.find(Log.collection)
        logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        if limit is not None:
            return logs[skip:skip + limit]
        return logs

    @staticmethod
    def find_filtered(level: Optional[str] = None,
                      log_type: Optional[str] = None,
                      username: Optional[str] = None,
                      search: Optional[str] = None,
                      skip: int = 0,
                      limit: int = None) -> List[Dict[str, Any]]:
        db = Log._get_db()

        def filter_func(log):
            if level and log.get("level") != level.lower():
                return False
            if log_type and log.get("log_type") != log_type.lower():
                return False
            if username and log.get("username") != username:
                return False
            if search and search.lower() not in log.get("message", "").lower():
                return False
            return True

        logs = db.find(Log.collection, filter_func)
        logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        if limit is not None:
            return logs[skip:skip + limit]
        return logs

    @staticmethod
    def count() -> int:
        db = Log._get_db()
        return db.count(Log.collection)
