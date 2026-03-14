#!/bin/bash
# OPASSIT 数据库备份
# 方式1: mysqldump（需 MySQL 用户有 RELOAD 权限）
# 方式2: Django dumpdata（使用应用配置，无需额外权限）
set -e
cd "$(dirname "$0")/.."

[ -f .env ] && set -a && source .env 2>/dev/null && set +a || true
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 优先尝试 mysqldump
if command -v mysqldump >/dev/null 2>&1; then
  DB_USER="${MYSQL_USER:-opassit}"
  DB_PASS="${MYSQL_PASSWORD:-opassit}"
  DB_HOST="${MYSQL_HOST:-localhost}"
  DB_PORT="${MYSQL_PORT:-3306}"
  DB_NAME="${MYSQL_DATABASE:-opassit}"
  BACKUP_FILE="$BACKUP_DIR/opassit_${TIMESTAMP}.sql"
  echo "=== mysqldump 备份 $DB_NAME 到 $BACKUP_FILE ==="
  export MYSQL_PWD="$DB_PASS"
  if mysqldump -u "$DB_USER" -h "$DB_HOST" -P "$DB_PORT" \
    --single-transaction --skip-lock-tables --no-tablespaces \
    "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
    unset MYSQL_PWD
    echo "备份完成: $BACKUP_FILE"
    ls -lh "$BACKUP_FILE"
    exit 0
  fi
  unset MYSQL_PWD
fi

# 回退: Django dumpdata
BACKUP_FILE="$BACKUP_DIR/opassit_data_${TIMESTAMP}.json"
echo "=== Django dumpdata 备份到 $BACKUP_FILE ==="
if [ -d .venv ]; then source .venv/bin/activate; fi
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission \
  -o "$BACKUP_FILE" 2>/dev/null || python manage.py dumpdata -o "$BACKUP_FILE"
echo "备份完成: $BACKUP_FILE"
ls -lh "$BACKUP_FILE"
