FROM percona/percona-xtrabackup:8.0.35

USER root

# Устанавливаем cron
RUN microdnf update -y && \
    microdnf install -y cronie && \
    microdnf clean all

COPY db_backup.sh /usr/local/bin/db_backup.sh
COPY db_restore.sh /usr/local/bin/db_restore.sh
COPY cleanup.sh /usr/local/bin/cleanup.sh

COPY cronjob /etc/cron.d/db-backup-cron

RUN chmod +x /usr/local/bin/db_backup.sh \
    /usr/local/bin/db_restore.sh \
    /usr/local/bin/cleanup.sh

# Даем права cronjob и регистрируем его
RUN chmod 0644 /etc/cron.d/db-backup-cron && crontab /etc/cron.d/db-backup-cron

RUN touch /var/log/cron.log

RUN touch /etc/container_environment && chmod 600 /etc/container_environment

# передаем пароль из окружения в файл, т.к. в cron не передаются переменные окружения
# Запускаем cron в фоне и tail лога, чтобы контейнер не завершился
CMD ["sh", "-c", "\
    env | grep -E '^(MYSQL_ROOT_PASSWORD)=' > /etc/container_environment && \
    crond -n -x sch,proc & tail -f /var/log/cron.log \
    "]


