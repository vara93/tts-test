#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"; exec > >(tee -a install.log) 2>&1
[[ $EUID == 0 ]] || { echo "Запустите через sudo bash ./install.sh"; exit 1; }
. /etc/os-release
[[ ${ID:-} == ubuntu ]] || { echo "Поддерживается Ubuntu, найдена ${ID:-unknown}"; exit 1; }
[[ $(uname -m) == x86_64 ]] || { echo "Требуется Linux x86_64"; exit 1; }
echo "Ubuntu ${VERSION_ID}; CPU: $(nproc); RAM: $(awk '/MemTotal/{printf "%.1f GiB",$2/1048576}' /proc/meminfo)"
echo "CPU flags: $(awk -F: '/flags/{print $2;exit}' /proc/cpuinfo)"
df -h .; ss -ltn | awk 'NR==1 || /:80 |:443 /' || true
command -v curl >/dev/null || { apt-get update; apt-get install -y ca-certificates curl; }
if ! command -v docker >/dev/null; then
  echo "Устанавливается Docker из репозитория Ubuntu ${VERSION_CODENAME} (без подмены codename)"
  apt-get update; apt-get install -y docker.io docker-compose-v2
fi
docker compose version >/dev/null || { echo "Docker Compose v2 отсутствует"; exit 1; }
mkdir -p data/{profiles,jobs,caddy,caddy-config} models
chmod 750 data models
if [[ ! -f .env ]]; then
  ip=$(hostname -I | awk '{print $1}'); pass=$(head -c 24 /dev/urandom | base64 | tr -d '\n')
  cat >.env <<EOF
STUDIO_PASSWORD=$pass
STUDIO_HOST=${STUDIO_HOST:-$ip}
HTTP_PORT=${HTTP_PORT:-80}
HTTPS_PORT=${HTTPS_PORT:-443}
TTS_DATA=/data
MODEL_REVISION=chatterbox-tts-0.1.6
HF_HUB_OFFLINE=0
EOF
  chmod 600 .env
fi
set -a; . ./.env; set +a
for host in pypi.org huggingface.co; do curl -fsSI --max-time 10 "https://$host" >/dev/null || { echo "Недоступен $host"; exit 1; }; done
docker compose build
docker compose run --rm -e HF_HUB_OFFLINE=0 worker python -c 'import soundfile as sf; from chatterbox.mtl_tts import ChatterboxMultilingualTTS as M; m=M.from_pretrained(device="cpu"); w=m.generate("Проверка локального синтеза на процессоре.",language_id="ru"); sf.write("/data/install-smoke.wav",w.squeeze().detach().cpu().numpy(),m.sr); print("Настоящий smoke WAV создан")'
docker compose up -d
for i in {1..30}; do curl -fkSs "https://${STUDIO_HOST}:${HTTPS_PORT}/api/health" >/dev/null && break; sleep 2; done
curl -fkSs "https://${STUDIO_HOST}:${HTTPS_PORT}/api/health" >/dev/null || { docker compose logs --tail=100; exit 1; }
echo "Интерфейс: https://${STUDIO_HOST}:${HTTPS_PORT}"
echo "Пароль: $STUDIO_PASSWORD"
echo "CA для клиентского устройства: data/caddy/pki/authorities/local/root.crt"
echo "ВАЖНО: импортируйте CA на КЛИЕНТСКОМ ПК; установка на сервере не создаёт доверия браузера."
echo "Диагностика: sudo bash ./doctor.sh; журнал: $(pwd)/install.log"
