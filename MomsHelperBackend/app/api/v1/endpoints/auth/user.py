import os
import jwt
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.database.tables.logs import Log
from app.database.tables.users import User
from app.database.tables.roles import Role
from app.api.v1.models.auth.user import UserCreate, UserLogin, Token, UserInDBWithRole, UserCreateResponse

router = APIRouter()
security = HTTPBearer()

secret_key = os.getenv("secret_key")
algorithm = os.getenv("algorithm")
access_token_expire_minutes = int(os.getenv("access_token_expire_minutes"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = User.find_by_username(username)
    if user is None or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def check_user_permissions(user: dict, required_permission: str) -> bool:
    if user.get("is_superuser"):
        return True
    if user.get("role_id"):
        role_id = str(user["role_id"]) if user["role_id"] is not None else None
        if role_id:
            role = Role.find_by_id(role_id)
            if role and role.get("permissions"):
                return required_permission in role["permissions"]
    return False


@router.get("/check-first-user")
def check_first_user():
    try:
        user_count = User.count()
        return {"has_users": user_count > 0}
    except Exception:
        return {"has_users": True}


@router.post("/register-first-user", response_model=UserInDBWithRole)
def register_first_user(user_data: UserCreate):
    try:
        user_count = User.count()
        if user_count > 0:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="First user already exists")

        existing_user = User.find_by_username(user_data.username)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        user_dict = user_data.dict()
        user_dict["is_superuser"] = True
        user_dict["role_id"] = None

        db_user = User.create(user_dict)

        Log.create(
            "system",
            "user",
            f"Создан первый пользователь: {db_user['username']}",
            db_user["id"],
            db_user["username"]
        )

        return db_user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating first user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error creating first user: {str(e)}")

@router.get("/users", response_model=List[UserInDBWithRole])
def get_users(request: Request, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "view_users"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостаточно прав для просмотра пользователей")

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "page_view",
        "Просмотр списка пользователей",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    users = User.find_all()
    result = []
    for user in users:
        user_copy = user.copy()
        if user_copy.get("role_id"):
            role_id = str(user_copy["role_id"])
            role = Role.find_by_id(role_id)
            if role:
                user_copy["role"] = role
            user_copy["role_id"] = role_id
        result.append(user_copy)

    return result


@router.get("/users/{user_id}", response_model=UserInDBWithRole)
def get_user(request: Request, user_id: str, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "view_users"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостаточно прав для просмотра пользователей")

    user = User.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user_copy = user.copy()
    if user_copy.get("role_id"):
        role_id = str(user_copy["role_id"])
        role = Role.find_by_id(role_id)
        if role:
            user_copy["role"] = role
        user_copy["role_id"] = role_id

    return user_copy


@router.post("/users", response_model=UserCreateResponse)
def create_user(request: Request, user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "manage_users"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостаточно прав для создания пользователей")

    existing_user = User.find_by_username(user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пользователь с таким логином уже существует")

    user_dict = user_data.dict()
    user_dict["is_superuser"] = False

    db_user = User.create(user_dict)

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "user",
        f"Создан новый пользователь: {db_user['username']} администратором {current_user['username']}",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    return db_user


@router.post("/login", response_model=Token)
def login(request: Request, user_data: UserLogin):
    user = User.find_by_username(user_data.username)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not User.verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    User.update_last_login(user["id"])

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "auth",
        f"Пользователь {user['username']} вошёл в систему",
        user["id"],
        user["username"],
        client_ip
    )

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserInDBWithRole)
def get_me(current_user: dict = Depends(get_current_user)):
    user_copy = current_user.copy()
    if user_copy.get("role_id"):
        role_id = str(user_copy["role_id"])
        role = Role.find_by_id(role_id)
        if role:
            user_copy["role"] = role
        user_copy["role_id"] = role_id
    return user_copy


@router.put("/users/{user_id}", response_model=UserInDBWithRole)
def update_user(request: Request, user_id: str, user_data: dict, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "manage_users"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостаточно прав для редактирования пользователей")

    user = User.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.get("is_superuser") and not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Нельзя редактировать главного администратора")

    if not current_user.get("is_superuser") and current_user.get("role_id"):
        current_role_id = str(current_user["role_id"])
        if user.get("role_id"):
            target_role_id = str(user["role_id"])
            if current_role_id == target_role_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Нельзя редактировать пользователя с такой же ролью")

    update_fields = {}
    if "lastName" in user_data:
        update_fields["lastName"] = user_data["lastName"]
    if "firstName" in user_data:
        update_fields["firstName"] = user_data["firstName"]
    if "middleName" in user_data:
        update_fields["middleName"] = user_data["middleName"]
    if "is_active" in user_data:
        update_fields["is_active"] = user_data["is_active"]
    if "role_id" in user_data:
        if not current_user.get("is_superuser") and current_user.get("role_id"):
            current_role_id = str(current_user["role_id"])
            if user_data["role_id"] and str(user_data["role_id"]) == current_role_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Нельзя назначить свою собственную роль")
        update_fields["role_id"] = user_data["role_id"] if user_data["role_id"] is not None else None
    if "password" in user_data and user_data["password"]:
        hashed_password = User.hash_password(user_data["password"])
        update_fields["hashed_password"] = hashed_password
        update_fields["is_temporary_password"] = False
        moscow_tz = timezone(timedelta(hours=3))
        update_fields["password_changed_at"] = datetime.now(moscow_tz).isoformat()

    moscow_tz = timezone(timedelta(hours=3))
    update_fields["last_activity"] = datetime.now(moscow_tz).isoformat()

    User.update(user_id, update_fields)
    updated_user = User.find_by_id(user_id)

    user_copy = updated_user.copy()
    if user_copy.get("role_id"):
        role_id = str(user_copy["role_id"])
        role = Role.find_by_id(role_id)
        if role:
            user_copy["role"] = role
        user_copy["role_id"] = role_id

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "user",
        f"Пользователь {user_copy['username']} обновлен администратором {current_user['username']}",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    return user_copy


@router.post("/users/{user_id}/toggle-status", response_model=UserInDBWithRole)
def toggle_user_status(request: Request, user_id: str, status_data: dict,
                       current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "toggle_user_status"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостаточно прав для изменения статуса пользователя")

    user = User.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.get("is_superuser") and not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Нельзя изменять статус главного администратора")

    if not current_user.get("is_superuser") and current_user.get("role_id"):
        current_role_id = str(current_user["role_id"])
        if user.get("role_id"):
            target_role_id = str(user["role_id"])
            if current_role_id == target_role_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Нельзя изменять статус пользователя с такой же ролью")

    if "is_active" in status_data:
        User.update(user_id, {"is_active": status_data["is_active"]})

    updated_user = User.find_by_id(user_id)

    user_copy = updated_user.copy()
    if user_copy.get("role_id"):
        role_id = str(user_copy["role_id"])
        role = Role.find_by_id(role_id)
        if role:
            user_copy["role"] = role
        user_copy["role_id"] = role_id

    action = "активирован" if user_copy["is_active"] else "деактивирован"
    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "user",
        f"Пользователь {user_copy['username']} {action} администратором {current_user['username']}",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    return user_copy


@router.post("/logout")
def logout(request: Request, current_user: dict = Depends(get_current_user)):
    moscow_tz = timezone(timedelta(hours=3))
    User.update_last_activity(current_user["id"])

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "auth",
        f"Пользователь {current_user['username']} вышел из системы",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    return {"message": "Successfully logged out"}
