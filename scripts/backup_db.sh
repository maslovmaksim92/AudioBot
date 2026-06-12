#!/usr/bin/env bash
# Ежедневный бэкап БД audiobot с ротацией.
# Хранит 14 дней. Логирует результат. Проверяет целостность дампа.
set -uo pipefail

BACKUP_DIR="/opt/audiobot/backups"
ENV_FILE="/opt/audiobot/backend/.env"
KEEP_DAYS=14
LOG="/var/log/audiobot_backup.log"

mkdir -p "$BACKUP_DIR"

DBURL=$(grep -oP '^DATABASE_URL=\K.*' "$ENV_FILE" | sed 's|postgresql+asyncpg://|postgresql://|; s|postgresql+psycopg://|postgresql://|')

TS=$(date '+%Y%m%d_%H%M%S')
OUT="$BACKUP_DIR/audiobot_${TS}.sql.gz"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') | $*" | tee -a "$LOG"; }

log "START backup -> $OUT"

if pg_dump "$DBURL" --no-owner --no-acl --clean --if-exists 2>>"$LOG" | gzip > "$OUT"; then
    SIZE=$(du -h "$OUT" | cut -f1)
    if gzip -t "$OUT" 2>>"$LOG"; then
        # Проверка наличия таблицы houses (без SIGPIPE: считаем совпадения)
        HOUSES_HIT=$(zcat "$OUT" | grep -cE "COPY public\.houses[ (]" || true)
        if [ "${HOUSES_HIT:-0}" -ge 1 ]; then
            log "OK backup done: $OUT ($SIZE) — целостность подтверждена (houses найдена)"
        else
            log "WARN backup $OUT не содержит таблицу houses — проверьте!"
        fi
    else
        log "ERROR gzip-проверка не прошла: $OUT — дамп повреждён!"
        rm -f "$OUT"
        exit 1
    fi
else
    log "ERROR pg_dump упал"
    rm -f "$OUT"
    exit 1
fi

DELETED=$(find "$BACKUP_DIR" -name 'audiobot_*.sql.gz' -mtime +$KEEP_DAYS -print -delete | wc -l)
log "ротация: удалено старых дампов: $DELETED (хранение $KEEP_DAYS дней)"

TOTAL=$(find "$BACKUP_DIR" -name 'audiobot_*.sql.gz' | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "END: всего бэкапов $TOTAL, занято $TOTAL_SIZE"
