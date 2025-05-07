#!/bin/bash

DEST="/backup"

# Сколько последних бэкапов хранить
RETENTION_COUNT=7

echo "[$(date)] Starting backup cleanup..."

# Список бэкапов, отсортированных по дате создания (новые первыми)
BACKUPS=($(ls -dt ${DEST}/*-full 2>/dev/null))

# Сколько всего бэкапов найдено
BACKUP_COUNT=${#BACKUPS[@]}

echo "[$(date)] Found ${BACKUP_COUNT} backups."

# Если бэкапов больше, чем нужно оставить
if (( BACKUP_COUNT > RETENTION_COUNT )); then
    DELETE_COUNT=$((BACKUP_COUNT - RETENTION_COUNT))
    echo "[$(date)] Deleting ${DELETE_COUNT} old backups..."

    for (( i=RETENTION_COUNT; i<BACKUP_COUNT; i++ )); do
        echo "[$(date)] Deleting: ${BACKUPS[$i]}"
        rm -rf "${BACKUPS[$i]}"
    done

    echo "[$(date)] Old backups deleted."
else
    echo "[$(date)] No old backups to delete."
fi

echo "[$(date)] Backup cleanup completed."
