# Cafe
Приложение для сбора и обработки информации из открытых источников о заведениях общественного питания и предоставления её посредством интерфейса telegram бота

ссылка на ТЗ:
https://docs.google.com/document/d/1ulcOVP7esgEitXVv6R4WnSrMcERbFtEJ6Nxwph68C90/edit?pli=1&tab=t.0

### Перед началом:

Рекомендуемые параметры системы - 2xCPU, 4 Gb RAM, от 30 Gb SSD
Приложение работает в docker-окружении - установить перед началом работы docker engine, docker-compose
Убедиться в доступности с выбранной машины сетевых сервисов (telegram, api.hikerapi.com, openai api)

### Переменные окружения (.env)

Переименовать `example.env` в `.env` и установить свои переменные окружения (не должно быть пустых строк, комментариев)

Обязательно установить свои сложные разные пароли от бд (`MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`).
При необходимости изменить название бд и имя ее пользователя (`MYSQL_DATABASE`, `MYSQL_USER`).

Для сбора данных из telegram каналов требуется получить собственный API ID и Hash. Это можно сделать пройдя по ссылке [https://my.telegram.org/auth?to=apps](https://my.telegram.org/auth?to=apps), указав номер телефона привязанный к профилю, и заполнив после авторизации поля App title и Short name. Platform - можно выбрать “Other (specify in description)”. Остальные параметры можно оставить пустыми.
По нажатию `Create application` станут доступны собственные API ID и Hash, которые нужно присвоить переменным `TG_API_ID` и `TG_API_HASH` соответственно.
При необходимости изменить параметр `TG_SESSION` - содержит название файла сессии telegram

Для сбора информации из instagram используется api сервис (платный) [hikerapi](https://hikerapi.com/p/bkXQlaVe). Токен, полученный на сайте указать в переменной `HIKER_API_ACCESS_KEY`

Для работы telegram бота (пользовательскийи интерфейс) требуется в .env файле указать токен, полученный  от BotFather, в переменной `TG_BOT_TOKEN`

Для обработки через LLM изменить при необходимости адрес и указать api ключ (`OPENAI_API_BASE`, `OPENAI_API_KEY`)

### Установка

1. Переименовать `example.env` в `.env` и установить свои переменные окружения
2. Создать том для хранения таблиц бд: `docker volume create db-data`
3. Создать и установить права для монтируемых папок: `docker compose -f docker-compose.init.yml up`
4. Собрать образы `docker compose build`
5. Создать сессию телеграм-авторизации: `docker compose run --rm collector uv run tg_sessions/session.py`
6. Выполнить миграцию бд: `docker compose -f docker-compose.yml -f docker-compose.migration.yml run --rm collector alembic upgrade head`
7. запустить сервисы: `docker compose -up -d`

### Обновление
1. Сделать бэкап бд
`docker exec -it db_backup db_backup.sh`
2. Пересобрать образы 
`docker compose build`
3. Остановить сервисы
`docker-compose down`
4. Накатить миграции 
`docker compose -f docker-compose.yml -f docker-compose.migration.yml run --rm collector alembic upgrade head`
5. Запустить сервисы
`docker compose up -d`

### Настройки
Установить источники данных и настроить расписание запуска задач можно через подключение к бд

### Резервирование данных
Бэкапы снимаются с помощью `percona xtrabackup`
Используется сжатие бэкапов
Ежедневное сохранение работает по расписанию в контейнере `backup`
Копии на хосте хранятся в `./backup_data`
Настройка количества хранимых бэкапов в файле `./backup/cleanup.sh` (7 после установки)
При изменении скриптов или расписания (все в `./backup`) нужно перезапустить образ с пересборкой:
`docker compose up --build backup -d`

Для автоматического бэкапа по запросу выполнить в контейнере: `docker exec -it db_backup db_backup.sh`

Для автоматического восстановления из последней (рассчитывается по дате в названии папки) копии:
1. Остановить все сервисы: `docker compose down`
2. запустить команду в контейнере восстановления: `docker compose run --rm -v db-data:/var/lib/mysql backup db_restore.sh`
3. Запустить сервисы: `docker compose up -d`

Работа с бэкапами также доступна в ручном режиме, через прямое обращение к `xtrabackup` в контейнере (см документацию [xtrabackup](https://docs.percona.com/percona-xtrabackup/8.0/index.html)).

## Разработчику

### Миграции
краткая инструкция по alembic:
#### Настройка alembic (при необходимости, в проекте уже настроено)
1. `alembic init migrations`
2. Поправить при необходимости `env.py` чтобы был доступ к бд, metadata и моделям

#### Проведение миграций
1. Создать
`alembic revision --autogenerate -m "migration message"`
2. Проверить что получилось в папке  `migrations/versions`
3. Примененить к бд -  `alembic upgrade head`

в проекте миграции проводятся через контейнер `collector`, папки проброшены в файле `docker-compose.migration.yml`,
поэтому запуск команд будет выглядеть так (выполнять на остановленных сервисах):

`docker compose -f docker-compose.yml -f docker-compose.migration.yml run --rm collector alembic revision --autogenerate -m "init"`
`docker compose -f docker-compose.yml -f docker-compose.migration.yml run --rm collector alembic upgrade head`




