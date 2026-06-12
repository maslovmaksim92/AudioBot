"""
Централизованный конфиг логирования для audiobot.

Особенности:
- Ротация: /var/log/audiobot.log — основной (5×50МБ), /var/log/audiobot.err.log — только ошибки (3×20МБ).
- Stdout/stderr продолжают писать в /var/log/audiobot.log через systemd (см. service unit).
- request_id для корреляции запросов (см. middleware в server.py).
- Подавляем шум сторонних библиотек (httpx INFO -> WARNING), оставляя наш код INFO.

Уровни и куда что попадает:
  DEBUG  — только в файл (не на stdout), включается флагом DEBUG=1 в .env
  INFO   — основной поток наших событий
  WARNING/ERROR — дублируются в audiobot.err.log
"""
import os
import logging
import logging.handlers
from contextvars import ContextVar

LOG_DIR = "/var/log"
LOG_MAIN = os.path.join(LOG_DIR, "audiobot.log")
LOG_ERR  = os.path.join(LOG_DIR, "audiobot.err.log")

# request_id для корреляции (Set в middleware, Get в форматере)
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Подмешивает request_id в каждую запись."""
    def filter(self, record):
        record.req_id = request_id_var.get() or "-"
        return True


_LEVEL_DEBUG = os.environ.get("DEBUG", "0") == "1"


def setup_logging():
    """Вызывается один раз при старте процесса (в server.py)."""
    root = logging.getLogger()
    # Если уже настроено — не дублируем (на случай повторного импорта)
    if getattr(root, "_audiobot_configured", False):
        return
    root._audiobot_configured = True

    root.setLevel(logging.DEBUG if _LEVEL_DEBUG else logging.INFO)
    # очищаем дефолтные хендлеры uvicorn-bootstrap
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        "%(asctime)s [%(req_id)s] %(levelname).1s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    req_filter = RequestIdFilter()

    # 1) Основной файл с ротацией (5×50МБ = 250МБ макс)
    main_h = logging.handlers.RotatingFileHandler(
        LOG_MAIN, maxBytes=50 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    main_h.setLevel(logging.DEBUG if _LEVEL_DEBUG else logging.INFO)
    main_h.setFormatter(fmt)
    main_h.addFilter(req_filter)
    root.addHandler(main_h)

    # 2) Отдельный файл только для WARNING+ (3×20МБ = 60МБ)
    err_h = logging.handlers.RotatingFileHandler(
        LOG_ERR, maxBytes=20 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    err_h.setLevel(logging.WARNING)
    err_h.setFormatter(fmt)
    err_h.addFilter(req_filter)
    root.addHandler(err_h)

    # 3) Консоль — на случай ручного запуска
    cons_h = logging.StreamHandler()
    cons_h.setLevel(logging.INFO)
    cons_h.setFormatter(fmt)
    cons_h.addFilter(req_filter)
    root.addHandler(cons_h)

    # Подавляем шум третьих сторон (но оставляем их WARNING+)
    for noisy in ("httpx", "httpcore", "asyncio", "uvicorn.access",
                  "sqlalchemy.engine", "watchfiles"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Uvicorn error — оставляем INFO (видны старт/стоп)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    logging.getLogger("audiobot.startup").info(
        f"logging configured: main={LOG_MAIN} (5x50M), err={LOG_ERR} (3x20M), debug={_LEVEL_DEBUG}"
    )


def set_request_id(rid: str):
    request_id_var.set(rid)


def get_request_id() -> str:
    return request_id_var.get()
