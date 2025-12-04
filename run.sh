
#!/usr/bin/env bash
set -euo pipefail

export DB_HOST="${DB_HOST:-127.0.0.1}"
export DB_PORT="${DB_PORT:-3306}"
export DB_USER="${DB_USER:-root}"
export DB_PASSWORD="${DB_PASSWORD:-rootpwd}"
export DB_NAME="${DB_NAME:-embeddingsOpenCV}"

# Si quieres aplicar el schema también desde run.sh (opcional, el workflow ya lo hace):
# mysql -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" -p"${DB_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME}"
# mysql -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" < db/schema.sql

# Ejecuta tu app / script. Si tu app es Python:
# python -m src.build_embeddings --dataset "$(pwd)/dataset/raw"

# O si es otro entrypoint:
# python main.py
echo "[INFO] Ejecutando build_embeddings..."
python -m src.build_embeddings --dataset "$(pwd)/dataset/raw"
