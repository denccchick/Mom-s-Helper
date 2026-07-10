from typing import List
from datetime import datetime
from pydantic import BaseModel


class Permission(BaseModel):
    id: str
    name: str
    description: str
    category: str


class RoleCreate(BaseModel):
    name: str
    description: str
    permissions: List[str]


class RoleUpdate(BaseModel):
    name: str
    description: str
    permissions: List[str]


class RoleInDB(BaseModel):
    id: str
    name: str
    description: str
    permissions: List[str]
    created_at: datetime
    updated_at: datetime


AVAILABLE_PERMISSIONS = [
    Permission(
        id="view_users",
        name="Просмотр пользователей",
        description="Просмотр списка пользователей",
        category="Пользователи"
    ),
    Permission(
        id="manage_users",
        name="Управление пользователями",
        description="Создание, редактирование и удаление пользователей",
        category="Пользователи"
    ),
    Permission(
        id="edit_user_names",
        name="Редактирование ФИО пользователей",
        description="Изменение фамилии, имени и отчества пользователей",
        category="Пользователи"
    ),
    Permission(
        id="toggle_user_status",
        name="Изменение статуса пользователей",
        description="Активация и деактивация пользователей",
        category="Пользователи"
    ),
    Permission(
        id="assign_user_roles",
        name="Назначение ролей пользователям",
        description="Назначение ролей пользователям системы",
        category="Роли"
    ),
    Permission(
        id="view_roles",
        name="Просмотр ролей",
        description="Просмотр списка ролей",
        category="Роли"
    ),
    Permission(
        id="manage_roles",
        name="Управление ролями",
        description="Создание, редактирование и удаление ролей",
        category="Роли"
    ),
    Permission(
        id="view_dashboard",
        name="Просмотр панели управления",
        description="Доступ к основной панели управления",
        category="Система"
    ),
    Permission(
        id="view_monitoring",
        name="Просмотр мониторинга",
        description="Просмотр системного мониторинга и статистики",
        category="Система"
    ),
    Permission(
        id="view_logs",
        name="Просмотр логов",
        description="Просмотр системных логов",
        category="Логи"
    ),
    Permission(
        id="manage_logs",
        name="Управление логами",
        description="Очистка и удаление логов",
        category="Логи"
    ),
    Permission(
        id="view_areas",
        name="Просмотр производственных площадок",
        description="Просмотр списка производственных площадок",
        category="Производство"
    ),
    Permission(
        id="manage_areas",
        name="Управление производственными площадками",
        description="Создание, редактирование и удаление производственных площадок",
        category="Производство"
    ),
    Permission(
        id="view_equipment",
        name="Просмотр оборудования",
        description="Просмотр списка оборудования",
        category="Производство"
    ),
    Permission(
        id="manage_equipment",
        name="Управление оборудованием",
        description="Создание, редактирование и удаление оборудования",
        category="Производство"
    ),
    Permission(
        id="view_measurements",
        name="Просмотр измерений",
        description="Просмотр списка измерений и статистики",
        category="Измерения"
    ),
    Permission(
        id="add_measurements",
        name="Добавление измерений",
        description="Добавление новых измерений",
        category="Измерения"
    ),
    Permission(
        id="edit_measurements",
        name="Редактирование измерений",
        description="Редактирование существующих измерений",
        category="Измерения"
    ),
    Permission(
        id="delete_measurements",
        name="Удаление измерений",
        description="Удаление измерений",
        category="Измерения"
    )
]
