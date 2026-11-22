# Установка на macOS

Команды выполняются из каталога `senimradar-ai`.

## Уже нужные инструменты

- Python 3.13
- Node.js и npm
- Git

Виртуальное окружение backend и зависимости frontend ставятся локально, без Homebrew.

## Backend

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Файл `.env` необязателен: без него используются локальные значения из кода. Их нельзя выносить на общий сервер.

Запуск:

```bash
source backend/.venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

`VITE_API_BASE_URL` по умолчанию — `http://127.0.0.1:8000`.

## MySQL

На этой машине работает MySQL Community Server 9.4.0 и принимает TCP на `127.0.0.1:3306`. MySQL Workbench — только клиент; для проекта нужен именно сервер. PostgreSQL не используется. Docker не нужен.

База проекта — `senimradar_ai`, кодировка `utf8mb4`. Пользователь приложения — `senimradar`. Ему выдаются права только на эту базу. Другие базы скрипт не открывает и не меняет.

Пароль в чат и в код не записывается. `scripts/setup-mysql.sh` кладёт его в локальные `backend/.env` и `backend/.mysql-init.sql`. Оба файла игнорируются Git.

```bash
chmod +x scripts/setup-mysql.sh
./scripts/setup-mysql.sh
```

Если переменная `MYSQL_ROOT_PASSWORD` не задана, скрипт не входит в MySQL от администратора. Тогда один раз в терминале:

```bash
mysql -u root -p < backend/.mysql-init.sql
cd backend
source .venv/bin/activate
alembic upgrade head
```

`mysql` спросит пароль администратора локально и не покажет его. После этого `/api/v1/health/ready` должен ответить `200`. Пока пользователь не создан, интерфейс показывает «База данных не запущена», а остальные страницы открываются.
