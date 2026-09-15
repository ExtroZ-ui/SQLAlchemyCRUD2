# Домашнее задание SQLAlchemy Core

В проекте реализованы подключение к PostgreSQL и функции CREATE, READ, UPDATE и DELETE для таблицы `users`. В изменяющих операциях используются явные транзакции, обработка исключений и `rollback()`.

## Подготовка базы данных

Создайте пустую базу данных PostgreSQL:

```sql
CREATE DATABASE sqlalchemy_homework;
```

## Установка и запуск

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg://postgres:ВАШ_ПАРОЛЬ@localhost:5432/sqlalchemy_homework"
python sqlalchemy_crud.py
python sqlalchemy_crud.py --demo
```

Первый запуск проверяет подключение и создаёт таблицу `users`. Запуск с параметром `--demo` последовательно демонстрирует все CRUD-операции.

## Структура таблицы

- `id` — первичный ключ;
- `name` — имя пользователя;
- `email` — уникальный адрес электронной почты;
- `age` — возраст от 0 до 150 лет.
