#!/usr/bin/env sh

set -eu

PROJECT_DIR="/mediall_en"
CONTAINER_NAME="mediall_en_web"

cd "$PROJECT_DIR"

echo "[deploy] Validating the updated application..."
docker exec "$CONTAINER_NAME" python manage.py check

echo "[deploy] Applying database migrations..."
docker exec "$CONTAINER_NAME" python manage.py migrate --noinput

echo "[deploy] Collecting static files..."
docker exec "$CONTAINER_NAME" python manage.py collectstatic --noinput

echo "[deploy] Restarting $CONTAINER_NAME..."
docker restart "$CONTAINER_NAME" >/dev/null

echo "[deploy] Waiting for the application health check..."
attempt=1
while [ "$attempt" -le 30 ]; do
    if curl --fail --silent --show-error \
        --output /dev/null \
        "http://127.0.0.1:6000/admin/login/"; then
        echo "[deploy] Deployment completed successfully."
        exit 0
    fi
    attempt=$((attempt + 1))
    sleep 1
done

echo "[deploy] Health check failed after 30 attempts." >&2
exit 1
