#!/bin/bash
set -e
DATADIR="/var/lib/mysql"
DEST="/backup"

LAST_FULL=$(ls -1 ${DEST} | grep -- '-full$' | sort | tail -n1 || true)

if [[ -n "$LAST_FULL" ]]; then
    TARGET_DIR="${DEST}/${LAST_FULL}/"
    xtrabackup --decompress --target-dir=${TARGET_DIR} --parallel=4
    xtrabackup --prepare --target-dir=${TARGET_DIR}
    rm -rf ${DATADIR}/*
    xtrabackup --copy-back --target-dir=${TARGET_DIR} --datadir=${DATADIR}
    chown -R mysql:mysql /var/lib/mysql
else
    echo "No full backup found in ${DEST}"
fi
