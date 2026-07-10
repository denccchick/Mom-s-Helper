from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any


class LogLevel(str, Enum):
    system = "system"
    info = "info"
    warning = "warning"
    error = "error"
    debug = "debug"


class LogType(str, Enum):
    auth = "auth"
    user = "user"
    role = "role"
    page_view = "page_view"
    action = "action"
    other = "other"


class LogInDB(BaseModel):
    id: str
    level: LogLevel
    log_type: LogType
    message: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


class LogFilter(BaseModel):
    level: Optional[LogLevel] = None
    log_type: Optional[LogType] = None
    username: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None
