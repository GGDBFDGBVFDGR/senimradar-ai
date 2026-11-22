#!/usr/bin/env bash
# Creates only the senimradar_ai database and the senimradar account.
# Does not list, alter, or drop any other database.
# The application password is written to gitignored files and is not printed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
ENV_FILE="$BACKEND/.env"
SQL_FILE="$BACKEND/.mysql-init.sql"
EXAMPLE="$BACKEND/.env.example"

if [[ ! -f "$ENV_FILE" || ! -f "$SQL_FILE" ]]; then
  python3 - "$ENV_FILE" "$SQL_FILE" "$EXAMPLE" <<'PY'
import secrets
import sys
from pathlib import Path
from urllib.parse import quote

env_path, sql_path, example_path = map(Path, sys.argv[1:4])
password = secrets.token_urlsafe(24)
example = example_path.read_text(encoding="utf-8")
env_path.write_text(
    example.replace("CHANGE_ME", quote(password, safe="")),
    encoding="utf-8",
)
env_path.chmod(0o600)
sql = f"""-- SenimRadar AI only. Does not touch other databases.
CREATE DATABASE IF NOT EXISTS senimradar_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'senimradar'@'127.0.0.1' IDENTIFIED BY '{password}';
CREATE USER IF NOT EXISTS 'senimradar'@'localhost' IDENTIFIED BY '{password}';
ALTER USER 'senimradar'@'127.0.0.1' IDENTIFIED BY '{password}';
ALTER USER 'senimradar'@'localhost' IDENTIFIED BY '{password}';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES
  ON senimradar_ai.* TO 'senimradar'@'127.0.0.1';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES
  ON senimradar_ai.* TO 'senimradar'@'localhost';
FLUSH PRIVILEGES;
"""
sql_path.write_text(sql, encoding="utf-8")
sql_path.chmod(0o600)
PY
fi

if [[ -z "${MYSQL_ROOT_PASSWORD:-}" ]]; then
  echo "Для создания базы senimradar_ai нужны права администратора MySQL."
  echo "Пароль приложения уже записан в локальный backend/.env и не выводится сюда."
  echo "Выполните в терминале, пароль root MySQL скрипт не печатает:"
  echo "  mysql -u root -p < backend/.mysql-init.sql"
  echo "Затем:"
  echo "  cd backend && source .venv/bin/activate && alembic upgrade head"
  exit 2
fi

mysql --protocol=TCP -h 127.0.0.1 -u root -p"${MYSQL_ROOT_PASSWORD}" < "$SQL_FILE"
echo "База senimradar_ai и пользователь senimradar подготовлены."
