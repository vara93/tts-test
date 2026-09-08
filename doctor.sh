#!/usr/bin/env bash
set -u; cd "$(dirname "$0")"; fail=0
check(){ printf '%-32s' "$1"; shift; if "$@" >/dev/null 2>&1; then echo OK; else echo FAIL; fail=1; fi; }
echo "CPU=$(nproc), RAM=$(free -h | awk '/Mem:/{print $2}'), disk=$(df -h . | awk 'NR==2{print $4}')"
check "x86_64" test "$(uname -m)" = x86_64
check "Docker" docker info
check "Compose" docker compose version
check "Конфигурация" test -s .env
check "Хранилище" test -w data
check "Контейнеры" docker compose ps --status running
set -a; [[ -f .env ]] && . ./.env; set +a
check "HTTPS/API" curl -fkSs --max-time 10 "https://${STUDIO_HOST:-localhost}:${HTTPS_PORT:-443}/api/health"
check "Файлы модели" test -n "$(find models -type f -print -quit 2>/dev/null)"
docker compose exec -T web ffmpeg -version | head -1 || fail=1
exit $fail
