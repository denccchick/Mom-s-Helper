import os
import jwt
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database.tables.logs import Log
from app.database.tables.roles import Role
from app.database.tables.users import User
from app.api.v1.models.auth.role import RoleCreate, RoleUpdate, RoleInDB, Permission, AVAILABLE_PERMISSIONS

router = APIRouter()
security = HTTPBearer()

algorithm = os.getenv("algorithm")
secret_key = os.getenv("secret_key")


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
        role = Role.find_by_id(user["role_id"])
        if role and role.get("permissions"):
            return required_permission in role["permissions"]
    return False


@router.get("/permissions", response_model=List[Permission])
def get_permissions():
    return AVAILABLE_PERMISSIONS


@router.get("/", response_model=List[RoleInDB])
def get_roles(request: Request, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "view_roles"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ролей")

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "page_view",
        "Просмотр списка ролей",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    return Role.find_all()


@router.post("/", response_model=RoleInDB)
def create_role(request: Request, role_data: RoleCreate, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "manage_roles"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для создания ролей")

    existing_role = Role.find_by_name(role_data.name)
    if existing_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Роль с таким названием уже существует")

    valid_permissions = [p.id for p in AVAILABLE_PERMISSIONS]
    for perm in role_data.permissions:
        if perm not in valid_permissions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Неизвестное право: {perm}")

    role_dict = role_data.dict()
    db_role = Role.create(role_dict)

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "role",
        f"Создана новая роль: {db_role['name']} администратором {current_user['username']}",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    return db_role


@router.get("/{role_id}", response_model=RoleInDB)
def get_role(request: Request, role_id: str, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "view_roles"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ролей")

    role = Role.find_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")

    return role


@router.put("/{role_id}", response_model=RoleInDB)
def update_role(request: Request, role_id: str, role_data: RoleUpdate, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "manage_roles"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для редактирования ролей")

    role = Role.find_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")

    existing_role = Role.find_by_name(role_data.name)
    if existing_role and existing_role["id"] != role_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Роль с таким названием уже существует")

    valid_permissions = [p.id for p in AVAILABLE_PERMISSIONS]
    for perm in role_data.permissions:
        if perm not in valid_permissions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Неизвестное право: {perm}")

    update_dict = role_data.dict()
    Role.update(role_id, update_dict)
    updated_role = Role.find_by_id(role_id)

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "role",
        f"Обновлена роль: {updated_role['name']} администратором {current_user['username']}",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    return updated_role


@router.delete("/{role_id}")
def delete_role(request: Request, role_id: str, current_user: dict = Depends(get_current_user)):
    if not check_user_permissions(current_user, "manage_roles"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для удаления ролей")

    role = Role.find_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")

    role_name = role["name"]
    Role.delete(role_id)

    client_ip = request.client.host if request.client else None

    Log.create(
        "system",
        "role",
        f"Удалена роль: {role_name} администратором {current_user['username']}",
        current_user["id"],
        current_user["username"],
        client_ip
    )

    return {"message": "Роль удалена"}
