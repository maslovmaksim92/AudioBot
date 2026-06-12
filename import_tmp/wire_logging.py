p = '/opt/audiobot/backend/server.py'
s = open(p, encoding='utf-8').read()

# 1) Заменяем basicConfig на setup_logging()
OLD = '''logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("server")'''
NEW = '''# Централизованное логирование (ротация, request_id, отдельный файл ошибок)
from backend.app.config.logging_config import setup_logging, set_request_id
setup_logging()
logger = logging.getLogger("server")'''
assert OLD in s, "блок basicConfig не найден"
s = s.replace(OLD, NEW)

# 2) Middleware: request_id + лог HTTP-обращений + поимка исключений
# Вставляем сразу после add_middleware(CORS...)
ANCHOR = '''app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)'''
ADD = ANCHOR + '''


# --- HTTP логирование: request_id + время + статус + исключения ---
import time as _time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from secrets import token_hex


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("X-Request-Id") or token_hex(4)
        set_request_id(rid)
        path = request.url.path
        # пропускаем шумный health-чек MAX каждые ~10 сек
        skip_log = path in ("/api/max/health", "/api/health")
        method = request.method
        client = request.client.host if request.client else "-"
        if not skip_log:
            logger.info(f"HTTP→ {method} {path} from={client}")
        t0 = _time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as e:
            dur = (_time.perf_counter() - t0) * 1000
            logger.exception(f"HTTP✗ {method} {path} 500 in {dur:.0f}ms — {type(e).__name__}: {e}")
            return JSONResponse({"error": "Internal Server Error", "request_id": rid}, status_code=500)
        dur = (_time.perf_counter() - t0) * 1000
        if not skip_log or response.status_code >= 400:
            level = logger.warning if response.status_code >= 400 else logger.info
            level(f"HTTP← {method} {path} {response.status_code} in {dur:.0f}ms")
        # ответ-эхо для отладки клиентом
        response.headers["X-Request-Id"] = rid
        return response


app.add_middleware(RequestLogMiddleware)
'''
assert ANCHOR in s, "CORS-middleware блок не найден"
s = s.replace(ANCHOR, ADD, 1)

open(p, 'w', encoding='utf-8').write(s)
print("OK: setup_logging + RequestLogMiddleware подключены")
