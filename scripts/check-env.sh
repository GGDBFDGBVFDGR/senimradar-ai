#!/usr/bin/env bash
set -u
echo "SenimRadar AI — проверка окружения"
echo "macOS: $(sw_vers -productVersion) ($(uname -m))"
python3 --version || echo "python3: missing"
node --version || echo "node: missing"
npm --version || echo "npm: missing"
git --version || echo "git: missing"
if command -v psql >/dev/null 2>&1; then
  psql --version
else
  echo "psql: not installed"
fi
if command -v docker >/dev/null 2>&1; then
  docker --version
else
  echo "docker: not installed"
fi
if command -v pg_isready >/dev/null 2>&1 && pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
  echo "postgres: accepting connections on 127.0.0.1:5432"
else
  echo "postgres: not accepting connections on 127.0.0.1:5432"
fi
