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

## PostgreSQL

На машине разработки PostgreSQL 14 принимает подключения на `127.0.0.1:5432`. Роль `senimradar` при этом не проходит аутентификацию, поэтому `alembic upgrade head` завершается ошибкой и таблицы не созданы. Docker не установлен. Этап 1 не создаёт роль и не меняет чужую базу.

Пока роль не создана, интерфейс показывает «База данных не запущена». Остальные страницы открываются. API при этом отвечает на `/api/v1/health`.

### Вариант с Docker

После отдельной установки Docker Desktop:

```bash
docker compose up -d
cd backend
source .venv/bin/activate
alembic upgrade head
```

Compose публикует PostgreSQL 16 только на `127.0.0.1:5432`.

### Вариант с Homebrew

PostgreSQL 14 уже стоит. Запуск службы меняет состояние macOS, поэтому его нужно включить отдельно:

```bash
brew services start postgresql@14
createuser senimradar
createdb -O senimradar senimradar
psql -d senimradar -c "ALTER USER senimradar WITH PASSWORD 'senimradar';"
```

Затем из `backend`:

```bash
source .venv/bin/activate
alembic upgrade head
```

Не запускайте Homebrew PostgreSQL и контейнер Compose одновременно: оба хотят порт 5432.

Локальный пароль `senimradar` не является боевым секретом. Перед любым общим сервером его нужно заменить через переменную `DATABASE_URL`.
