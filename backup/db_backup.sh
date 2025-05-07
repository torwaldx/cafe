#!/bin/bash
set -e

# Подгружаем окружение
set -a
[ -f /etc/container_environment ] && source /etc/container_environment
set +a

DEST="/backup"

STAMP=$(date +'%Y%m%d-%H%M%S')

TARGET_DIR="${DEST}/${STAMP}-full"

mkdir -p "${TARGET_DIR}"

echo "[$(date)] Starting backup: ${STAMP}"

xtrabackup --backup --compress \
    --datadir=/var/lib/mysql \
    --target-dir=${TARGET_DIR} \
    --user=root --password=${MYSQL_ROOT_PASSWORD}

echo "[$(date)] Backup completed successfully."


