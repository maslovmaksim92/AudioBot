#!/usr/bin/env bash
# Восстановление БД audiobot из бэкапа.
# ВНИМАНИЕ: перезаписывает текущую базу! Используйте осознанно.
# Запуск:
#   scripts/restore_db.sh                  — список доступных бэкапов
#   scripts/restore_db.sh <файл.sql.gz>    — восстановить из конкретного файла
#   scripts/restore_db.sh latest           — восстановить из самого свежего
set -uo pipefail

BACKUP_DIR="/opt/audiobot/backups"
ENV_FILE="/opt/audiobot/backend/.env"
DBURL=$(grep -oP '^DATABASE_URL=\K.*' "$ENV_FILE" | sed 's|postgresql+asyncpg://|postgresql://|; s|postgresql+psycopg://|postgresql://|')

ARG="${1:-}"

if [ -z "$ARG" ]; then
    echo "Доступные бэкапы:"
    ls -lht "$BACKUP_DIR"/audiobot_*.sql.gz 2>/dev/null | awk '{print "  "$9"  ("$5")"}'
    echo ""
    echo "Запуск: scripts/restore_db.sh <файл>   или   scripts/restore_db.sh latest"
    exit 0
fi

if [ "$ARG" = "latest" ]; then
    FILE=$(ls -t "$BACKUP_DIR"/audiobot_*.sql.gz 2>/dev/null | head -1)
else
    FILE="$ARG"
    [ -f "$FILE" ] || FILE="$BACKUP_DIR/$ARG"
fi

if [ ! -f "$FILE" ]; then
    echo "ОШИБКА: файл не найден: $FILE"
    exit 1
fi

echo "============================================================"
echo "ВНИМАНИЕ: будет ПЕРЕЗАПИСАНА текущая база audiobot!"
echo "Источник: $FILE ($(du -h "$FILE" | cut -f1))"
echo "============================================================"
read -p "Введите 'ДА' для подтверждения: " CONFIRM
if [ "$CONFIRM" != "ДА" ]; then
    echo "Отменено."
    exit 0
fi

# Страховочный бэкап текущего состояния ПЕРЕД восстановлением
echo "Делаю страховочный бэкап текущей базы..."
SAFETY="$BACKUP_DIR/pre_restore_$(date '+%Y%m%d_%H%M%S').sql.gz"
pg_dump "$DBURL" --no-owner --no-acl --clean --if-exists | gzip > "$SAFETY"
echo "Страховка сохранена: $SAFETY"

echo "Восстанавливаю из $FILE ..."
if zcat "$FILE" | psql "$DBURL" >/dev/null 2>&1; then
    echo "✅ Восстановление завершено."
    echo "Если что-то не так — откат: scripts/restore_db.sh $SAFETY"
else
    echo "❌ Ошибка восстановления. Текущая база может быть в промежуточном состоянии."
    echo "Откат: scripts/restore_db.sh $SAFETY"
    exit 1
fi
