#!/usr/bin/env bash
set -u
echo "SenimRadar AI — проверка окружения"
echo "macOS: $(sw_vers -productVersion) ($(uname -m))"
python3 --version || echo "python3: missing"
node --version || echo "node: missing"
npm --version || echo "npm: missing"
git --version || echo "git: missing"
if command -v mysql >/dev/null 2>&1; then
  mysql --version
else
  echo "mysql client: not installed"
fi
if nc -z 127.0.0.1 3306 >/dev/null 2>&1; then
  echo "mysql: accepting TCP connections on 127.0.0.1:3306"
else
  echo "mysql: not accepting TCP connections on 127.0.0.1:3306"
fi
if command -v docker >/dev/null 2>&1; then
  docker --version
else
  echo "docker: not installed"
fi
