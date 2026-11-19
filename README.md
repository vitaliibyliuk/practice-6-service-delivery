# Monitor · практична робота 6

Flask обслуговує два маршрути через Gunicorn. `/health` повертає JSON із прапорцем `ready`. `/version` повертає поле `revision`, яке в GitHub Actions дорівнює SHA вихідного коміту.

## Запуск на своєму комп’ютері

Потрібні Python 3.13, Docker і Docker Compose.

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-qa.txt
docker build --build-arg RELEASE_ID=local-vb -t practice6-monitor-vb:local .
docker compose up -d --wait --wait-timeout 25
```

У файлі `.env` можна змінити `SERVICE_IMAGE`, внутрішній `SERVICE_PORT` і `PUBLISHED_PORT`. У контейнері `RELEASE_ID` задає версію, а `READINESS` визначає відповідь `/health`. Значення `offline` повертає 503.

## Перевірка та діагностика

```bash
python -m pytest -q tests
python -m pytest -q checks --hosts="docker://$(docker compose ps -q monitor)"
python ops/verify.py local-vb --port 8194
docker compose logs --no-color monitor
```

У запитах на злиття GitHub Actions тестує API та збирає Linux-образ. Після оновлення `main` завдання розгортання завантажує зібраний образ з артефакту й публікує його в GHCR під хешем. Docker Compose, Testinfra та контрольні HTTP-запити вирішують, чи отримує образ тег `verified`. Після збою скрипт повертає попередній digest, повторює перевірки й завершує невдалу операцію кодом 1.

Артефакти запусків містять звіти JUnit, журнал збірки та логи контейнерів, створених під час розгортання. У GitHub Actions відкрийте **Monitor delivery** і натисніть **Run workflow**. Для першої відмови виберіть `broken-test`, для другої — `offline`. Перед другим прогоном перевірте наявність успішного запуску `main` з образом `verified`.

```bash
gh workflow run delivery.yml --ref main -f scenario=broken-test
gh workflow run delivery.yml --ref main -f scenario=offline
```

## Ручний відкат

Укажіть перевірений digest та SHA коміту. Для приватного пакета GHCR потрібен вхід з дозволом читання образу.

```bash
echo "Previous image reference:"
IFS= read -r SERVICE_IMAGE
export SERVICE_IMAGE
echo "Previous commit SHA:"
IFS= read -r PREVIOUS_REVISION
docker compose pull monitor
docker compose up -d --force-recreate --wait --wait-timeout 25
python ops/verify.py "$PREVIOUS_REVISION" --port 8194
docker compose down
```

## Розміщення

Навчальним середовищем є тимчасова Linux VM, де запускаються контейнер і перевірки. На IaaS той самий Compose можна перенести на постійну віртуальну машину й передати команді оновлення ОС і Docker. Для PaaS можна використати запуск контейнера з GHCR, а оновлення платформи виконує провайдер. У двох моделях команда обслуговує код та залежності образу. Обчислення, журнали, диски, реєстр і вихідний трафік формують витрати.
