# Battleship REST Service

REST-сервис для игры «Морской бой», реализованный на FastAPI с использованием PostgreSQL.

## Запуск проекта

Для запуска приложения и базы данных используется Docker Compose, нужно будет ввести:

```bash
docker compose up -d
```
После создания базы данных необходимо применить миграции: 
```bash
docker compose exec app alembic upgrade head
``` 
## Запуск тестов

А для прогона тестов используем:

```bash
docker compose exec app python -m pytest
```