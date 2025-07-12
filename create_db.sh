#!/usr/bin/env bash
## Script to create database in mysql
## Should be in project root and uses .env
set -ex
DEV_ENV=.env
if [[ -f "$DEV_ENV" ]]; then
    source $DEV_ENV
fi
cat <<-EOF > tmp_create.sql
DROP SCHEMA IF EXISTS ${MYSQL_DATABASE};
CREATE SCHEMA ${MYSQL_DATABASE} DEFAULT CHARACTER SET utf8mb4;
EOF
if [[ -f "$DEV_ENV" ]]; then
    # Remake DB in dev environment only
    mysql -u "${MYSQL_USER}" --password="${MYSQL_PASSWORD}" -h "${MYSQL_HOST}" < tmp_create.sql
    mysql -u "${MYSQL_USER}" --password="${MYSQL_PASSWORD}" -h "${MYSQL_HOST}" -e "SHOW SCHEMAS;" | grep "${MYSQL_DATABASE}"

    rm tmp_create.sql
else
    rm tmp_create.sql
    echo "upgrading DB"
    MIGRATIONS=migrations/
    if [[ ! -d "$MIGRATIONS" ]]; then
        echo "migrations directory not found"
        flask db init
    fi
    flask db migrate
    flask db upgrade
fi
