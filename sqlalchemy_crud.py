"""CRUD для PostgreSQL на SQLAlchemy Core.

Перед запуском задайте переменную окружения DATABASE_URL, например:
postgresql+psycopg://postgres:password@localhost:5432/sqlalchemy_homework
"""

from __future__ import annotations

import argparse
import logging
import os
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/sqlalchemy_homework",
)

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("email", String(255), nullable=False, unique=True),
    Column("age", Integer, nullable=False),
    CheckConstraint("age >= 0 AND age <= 150", name="ck_users_age"),
)


class DatabaseOperationError(RuntimeError):
    """Понятная прикладная ошибка при выполнении операции с БД."""


def create_postgres_engine(database_url: str = DATABASE_URL) -> Engine:
    """Создаёт Engine для PostgreSQL. Фактическое подключение выполняется лениво."""
    if not database_url.startswith(("postgresql+psycopg://", "postgresql://")):
        raise ValueError("Для задания требуется строка подключения к PostgreSQL")

    return create_engine(
        database_url,
        pool_pre_ping=True,
        echo=False,
    )


def init_db(engine: Engine) -> None:
    """Проверяет подключение и создаёт таблицу users, если она отсутствует."""
    try:
        with engine.begin() as connection:
            metadata.create_all(connection)
        logger.info("Таблица users готова к работе")
    except SQLAlchemyError as exc:
        logger.exception("Не удалось создать таблицу users")
        raise DatabaseOperationError("Ошибка инициализации базы данных") from exc


def create_user(engine: Engine, name: str, email: str, age: int) -> dict[str, Any]:
    """CREATE: добавляет пользователя и возвращает созданную запись."""
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            statement = (
                insert(users)
                .values(name=name, email=email, age=age)
                .returning(users)
            )
            created_user = dict(connection.execute(statement).mappings().one())
            transaction.commit()
            return created_user
        except IntegrityError as exc:
            transaction.rollback()
            logger.exception("Пользователь не создан: нарушено ограничение таблицы")
            raise DatabaseOperationError(
                "Проверьте уникальность email и допустимое значение age"
            ) from exc
        except SQLAlchemyError as exc:
            transaction.rollback()
            logger.exception("Ошибка при создании пользователя")
            raise DatabaseOperationError("Не удалось создать пользователя") from exc


def get_user(engine: Engine, user_id: int) -> dict[str, Any] | None:
    """READ: возвращает пользователя по id или None, если записи нет."""
    try:
        with engine.connect() as connection:
            statement = select(users).where(users.c.id == user_id)
            row = connection.execute(statement).mappings().one_or_none()
            return dict(row) if row is not None else None
    except SQLAlchemyError as exc:
        logger.exception("Ошибка при чтении пользователя id=%s", user_id)
        raise DatabaseOperationError("Не удалось получить пользователя") from exc


def get_all_users(engine: Engine) -> list[dict[str, Any]]:
    """READ: возвращает всех пользователей по возрастанию id."""
    try:
        with engine.connect() as connection:
            statement = select(users).order_by(users.c.id)
            rows = connection.execute(statement).mappings().all()
            return [dict(row) for row in rows]
    except SQLAlchemyError as exc:
        logger.exception("Ошибка при чтении списка пользователей")
        raise DatabaseOperationError("Не удалось получить список пользователей") from exc


def update_user(
    engine: Engine,
    user_id: int,
    *,
    name: str | None = None,
    email: str | None = None,
    age: int | None = None,
) -> dict[str, Any] | None:
    """UPDATE: изменяет переданные поля и возвращает обновлённую запись."""
    new_values = {
        key: value
        for key, value in {"name": name, "email": email, "age": age}.items()
        if value is not None
    }
    if not new_values:
        raise ValueError("Не переданы поля для обновления")

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            statement = (
                update(users)
                .where(users.c.id == user_id)
                .values(**new_values)
                .returning(users)
            )
            row = connection.execute(statement).mappings().one_or_none()
            transaction.commit()
            return dict(row) if row is not None else None
        except IntegrityError as exc:
            transaction.rollback()
            logger.exception("Пользователь id=%s не обновлён", user_id)
            raise DatabaseOperationError(
                "Проверьте уникальность email и допустимое значение age"
            ) from exc
        except SQLAlchemyError as exc:
            transaction.rollback()
            logger.exception("Ошибка при обновлении пользователя id=%s", user_id)
            raise DatabaseOperationError("Не удалось обновить пользователя") from exc


def delete_user(engine: Engine, user_id: int) -> bool:
    """DELETE: удаляет пользователя. Возвращает True, если запись существовала."""
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            statement = delete(users).where(users.c.id == user_id).returning(users.c.id)
            deleted_id = connection.execute(statement).scalar_one_or_none()
            transaction.commit()
            return deleted_id is not None
        except SQLAlchemyError as exc:
            transaction.rollback()
            logger.exception("Ошибка при удалении пользователя id=%s", user_id)
            raise DatabaseOperationError("Не удалось удалить пользователя") from exc


def run_demo(engine: Engine) -> None:
    """Последовательно демонстрирует все CRUD-операции."""
    created = create_user(engine, "Анна Смирнова", "anna@example.com", 25)
    print("CREATE:", created)

    found = get_user(engine, created["id"])
    print("READ ONE:", found)
    print("READ ALL:", get_all_users(engine))

    updated = update_user(engine, created["id"], age=26)
    print("UPDATE:", updated)

    deleted = delete_user(engine, created["id"])
    print("DELETE:", deleted)


def main() -> None:
    parser = argparse.ArgumentParser(description="SQLAlchemy Core CRUD для PostgreSQL")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="выполнить демонстрацию CREATE, READ, UPDATE и DELETE",
    )
    args = parser.parse_args()

    engine = create_postgres_engine()
    init_db(engine)
    if args.demo:
        run_demo(engine)
    else:
        print("Подключение успешно. Таблица users готова.")
        print("Для демонстрации CRUD запустите файл с параметром --demo.")
    engine.dispose()


if __name__ == "__main__":
    main()
