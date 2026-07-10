from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from app.database.connection import get_db, JSONDatabase


class Role:
    COLLECTION = "roles"

    @staticmethod
    def _get_db() -> JSONDatabase:
        return next(get_db())

    @staticmethod
    def find_by_id(role_id: str) -> Optional[Dict[str, Any]]:
        db = Role._get_db()
        return db.find_one(Role.COLLECTION, lambda r: r["id"] == role_id)

    @staticmethod
    def find_by_name(name: str) -> Optional[Dict[str, Any]]:
        db = Role._get_db()
        return db.find_one(Role.COLLECTION, lambda r: r["name"] == name)

    @staticmethod
    def find_all() -> List[Dict[str, Any]]:
        db = Role._get_db()
        return db.find(Role.COLLECTION)

    @staticmethod
    def create(role_data: Dict[str, Any]) -> Dict[str, Any]:
        db = Role._get_db()

        moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(moscow_tz).isoformat()

        role = {
            "name": role_data["name"],
            "description": role_data["description"],
            "permissions": role_data.get("permissions", []),
            "created_at": now,
            "updated_at": now
        }

        return db.insert(Role.COLLECTION, role)

    @staticmethod
    def update(role_id: str, update_data: Dict[str, Any]) -> int:
        db = Role._get_db()

        moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(moscow_tz).isoformat()
        update_data["updated_at"] = now

        return db.update(
            Role.COLLECTION,
            lambda r: r["id"] == role_id,
            lambda r: r.update(update_data)
        )

    @staticmethod
    def delete(role_id: str) -> int:
        db = Role._get_db()
        return db.delete(
            Role.COLLECTION,
            lambda r: r["id"] == role_id
        )
