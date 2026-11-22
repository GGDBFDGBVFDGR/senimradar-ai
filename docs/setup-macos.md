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

## Распознавание скриншота

Нужен macOS с Apple Vision и компилятор Swift из Xcode Command Line Tools. На этой машине это `/usr/bin/swiftc`, Swift 6.0.2. Отдельный языковой пакет скачивать не нужно.

При первом запросе API собирает `backend/app/ocr/vision_ocr` из `vision_ocr.swift`. Готовый файл в Git не входит. Если `swiftc` нет, раздел скриншота отвечает `503` с кодом `ocr_not_available`.

Проверка:

```bash
xcrun swiftc --version
```

22 ноября 2026 установлен Tesseract 5.5.4, лицензия Apache-2.0. Полный пакет `tesseract-lang` не ставился: он скачивает все языки. Отдельно добавлены только `kaz.traineddata` (7.2 МБ) и `rus.traineddata` (15 МБ) из `tessdata_best`, тоже Apache-2.0.

```bash
brew install tesseract
curl -L -o "$(brew --prefix)/share/tessdata/kaz.traineddata" https://github.com/tesseract-ocr/tessdata_best/raw/main/kaz.traineddata
curl -L -o "$(brew --prefix)/share/tessdata/rus.traineddata" https://github.com/tesseract-ocr/tessdata_best/raw/main/rus.traineddata
tesseract --list-langs
```

Проверка показала `eng`, `kaz`, `osd` и `rus`. Русский режим скриншота по-прежнему использует Apple Vision. Казахский режим использует Tesseract `kaz+rus`. Подробности в [stage-3-1.md](stage-3-1.md).
